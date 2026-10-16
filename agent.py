from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import List, TypedDict, Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from fatsecret_diary import get_daily_totals, is_fatsecret_connected


MODEL = ChatOllama(
    model="qwen3.5:4b",
    base_url="http://127.0.0.1:11434",
    temperature=0.3,
    num_ctx=4096,
    num_predict=1600,
    reasoning=False,
)

class NutritionNeeds(BaseModel):
    calories: int = Field(description="Daily calorie target in kcal")
    protein: float = Field(description="Daily protein target in grams")
    fat: float = Field(description="Daily fat target in grams")
    carbohydrates: float = Field(
        description="Daily carbohydrate target in grams"
    )

class Recipe(BaseModel):
    title: str = Field(..., description="Title of a recipe")
    description: str = Field(
        ...,
        description="2-3 sentence explanation (ingredients and count of kcal, protein, carbs and fat per serving + weight of serving)",
    )

class RecipeList(BaseModel):
    recipes: List[Recipe]

class State(TypedDict):
    topic: str
    recipes: List[Recipe]
    approval: str
    allergies: List[str]
    category: str

prompt = ChatPromptTemplate.from_template("""
You are a professional nutrition-focused recipe assistant.

Follow the meal scope specified in Requirements.

Category: {category}
Allergies: {allergies}
Requirements: {requirements}

Never include ingredients the user is allergic to.
Include approximate calories, protein, carbs, fat,
ingredients and serving weight.

{format_instructions}

Output only valid JSON matching the schema.
""")

parser = PydanticOutputParser(pydantic_object=RecipeList)

chain = prompt | MODEL | parser


@tool
def get_fatsecret_totals() -> dict:
    """Получить калории, белки, жиры и углеводы,
    записанные в FatSecret за сегодня."""
    print("[DEBUG] Вызван get_fatsecret_totals")
    return get_daily_totals()

@tool
def generate_recipes(
    category: str,
    allergies: str = "none",
    requirements: str = "none"
) -> str:
    """Generate three recipes based on the user's request.
    Use this tool when the user asks for recipes or meal ideas.
    category: Type of food, meal, or cuisine.
    allergies: Ingredients the user is allergic to.
    requirements: Calories, macros, dietary preferences, or other constraints.
    """
    print("[DEBUG] Вызван generate_recipes")
    return generate_recipe_text(category, allergies, requirements)


def generate_recipe_text(
    category: str,
    allergies: str,
    requirements: str,
) -> str:
    result = chain.invoke({
        "category": category,
        "allergies": allergies,
        "requirements": requirements,
        "format_instructions": parser.get_format_instructions(),
    })

    return "\n\n".join(
        f"{i}. {recipe.title}\n{recipe.description}"
        for i, recipe in enumerate(result.recipes, 1)
    )

@tool
def calculate_macronutrients_per_day(
        weight: float,
        height: float,
        activity: str = "average",
        goal: str = "maintain",
        gender: str = "female",
        illness: str = "none",
) -> str:
    """Calculate the person's daily calorie and macronutrient needs (protein, fat, and carbohydrates) based on the provided information. You may ask follow-up questions if essential information is missing before calculating the final estimates.

Args:
    weight: The person's weight in kilograms.
    height: The person's height in centimeters.
    activity: The person's physical activity level.
    goal: The person's goal (e.g., weight loss, weight maintenance, or muscle gain).
    gender: The person's sex, if required by the calculation formula.
    illness: Any relevant medical conditions that may affect nutritional recommendations.
"""
    print("[DEBUG] Вызван calculate_macronutrients_per_day")

@tool
def create_meal_plan(
    calorie_macronutrient_needs: NutritionNeeds,
    allergies: str = "none",
    category: str = "balanced meals",
) -> str:
    """Create a full-day meal plan based on daily calorie
    and macronutrient targets. Do not use FatSecret.

    Args:
        calorie_macronutrient_needs: Daily calorie and macro targets.
        allergies: User allergies.
        category: Preferred food type or cuisine.
    """
    needs = calorie_macronutrient_needs

    requirements = (
        "Create a FULL-DAY meal plan, not just one meal. "
        "Include breakfast, lunch, dinner and snacks. "
        f"Daily target: {needs.calories} kcal, "
        f"{needs.protein} g protein, {needs.fat} g fat, "
        f"{needs.carbohydrates} g carbohydrates. "
        "Include approximate calories and macros for each meal "
        "and the estimated daily total."
    )
    print("[DEBUG] Вызван create_meal_plan")
    return generate_recipe_text(category, allergies, requirements)

@tool
def create_meal(
    calorie_macronutrient_needs: NutritionNeeds,
    allergies: str = "none",
    category: str = "a meal",
    consumed_calories: float | None = None,
    consumed_protein: float | None = None,
    consumed_fat: float | None = None,
    consumed_carbohydrates: float | None = None,
) -> str:
    """Generate meal options for the rest of today.

    Use FatSecret if connected. Otherwise use manually provided
    consumed values. If consumed values are unknown, ask the user.

    Args:
        calorie_macronutrient_needs: Daily calorie and macro targets.
        allergies: User allergies.
        category: Desired meal or cuisine.
        consumed_calories: Calories already consumed today.
        consumed_protein: Protein already consumed today in grams.
        consumed_fat: Fat already consumed today in grams.
        consumed_carbohydrates: Carbs already consumed today in grams.
    """
    needs = calorie_macronutrient_needs
    print("[DEBUG] is_fatsecret_connected():", is_fatsecret_connected())
    if is_fatsecret_connected():
        try:
            totals = get_daily_totals()
            consumed_calories = totals["calories"]
            consumed_protein = totals["protein"]
            consumed_fat = totals["fat"]
            consumed_carbohydrates = totals["carbohydrate"]
        except Exception:
            return (
                "FatSecret is connected but today's diary could not "
                "be retrieved. Ask the user for today's consumed "
                "calories and macros, then try again."
            )

    consumed = [
        consumed_calories,
        consumed_protein,
        consumed_fat,
        consumed_carbohydrates,
    ]

    if any(value is None for value in consumed):
        return (
            "Today's consumed calories and macros are unknown. "
            "Ask the user how much they have eaten today before "
            "generating meal options."
        )

    remaining_calories = max(0, needs.calories - consumed_calories)
    remaining_protein = max(0, needs.protein - consumed_protein)
    remaining_fat = max(0, needs.fat - consumed_fat)
    remaining_carbs = max(
        0, needs.carbohydrates - consumed_carbohydrates
    )

    print("[DEBUG] Daily targets:", needs.model_dump())
    print("[DEBUG] Consumed:", {
        "calories": consumed_calories,
        "protein": consumed_protein,
        "fat": consumed_fat,
        "carbohydrates": consumed_carbohydrates,
    })
    print("[DEBUG] Remaining:", {
        "calories": remaining_calories,
        "protein": remaining_protein,
        "fat": remaining_fat,
        "carbohydrates": remaining_carbs,
    }
    )


    requirements = (
        "Generate meal options for the REST OF TODAY, not a full-day plan. "
        f"Daily targets: {needs.calories} kcal, {needs.protein} g protein, "
        f"{needs.fat} g fat, {needs.carbohydrates} g carbohydrates. "
        f"Already consumed: {consumed_calories:.0f} kcal, "
        f"{consumed_protein:.1f} g protein, {consumed_fat:.1f} g fat, "
        f"{consumed_carbohydrates:.1f} g carbohydrates. "
        f"Remaining: {remaining_calories:.0f} kcal, "
        f"{remaining_protein:.1f} g protein, "
        f"{remaining_fat:.1f} g fat, "
        f"{remaining_carbs:.1f} g carbohydrates. "
        "Generate three meal options that approximately fit the remaining "
        "targets. Do not treat the remaining daily calories as the target "
        "for each individual option."
    )
    print("[DEBUG] Вызван create_meal")
    return generate_recipe_text(category, allergies, requirements)

def collect_info(state:State) -> dict:
    print("Collecting some info for better recipes! Meow :3")
    allergies_input = input("Do you have any allergies? (if you do, write them down using ',' as split item/no\n> ").strip()
    category = input("Which type of recipe would you like to know?\n> ").strip()
    if allergies_input.lower() in ("no", "нет", ""):
        allergies = []
    else:
        allergies = [
            allergy.strip()
            for allergy in allergies_input.split(",")
            if allergy.strip()
        ]
    return {
        "allergies": allergies,
        "category": category if category else "whichever",
    }

def ask_approval(state: State) -> dict:
    print("\nGenerated recipes:")
    for i, st in enumerate(state["recipes"], 1):
        print(f"{i}. {st.title} - {st.description}")
    ans = input("\nDo you accept these? (yes/no)\n> ")
    return {"approval": ans.strip().lower()}

def route(state: State) -> Literal["generate", "__end__"]:
    return END if state.get("approval", "").startswith("y") else "generate"

# ------------------------- AGENT -------------------------
agent = create_react_agent(
    model=MODEL,
    tools=[generate_recipes, calculate_macronutrients_per_day, get_fatsecret_totals, create_meal_plan, create_meal],
    prompt="""
You are a helpful fitness and nutrition assistant.

Understand the user's request.
Use the recipe generation tool when recipes or meal ideas
are requested. Extract the category, allergies, and dietary
requirements from the user's message.

If important information is missing, ask a question.
For general nutrition questions, answer directly.
Never claim to have calculated or verified something
unless you actually have.

Use create_meal_plan when the user asks for a full-day meal plan
based on daily calorie and macronutrient targets.

Use create_meal when the user asks what to eat today, for lunch,
dinner, or another meal and wants the recommendation to account
for food already consumed.

For create_meal, use FatSecret if connected. If it is not connected
and consumed amounts are unknown, ask the user first.

Use calculate_macronutrients_per_day when daily targets are unknown.

IMPORTANT: Keep daily nutrition targets and consumed nutrition values strictly separate.

get_fatsecret_totals returns ONLY the food consumed today. These values are NOT daily targets.

calculate_macronutrients_per_day calculates the user's daily calorie and macronutrient targets.

Never use FatSecret totals as the calorie_macronutrient_needs argument of create_meal or create_meal_plan.

Before calling create_meal, obtain daily targets from calculate_macronutrients_per_day if they are not already known.

Pass daily targets as calorie_macronutrient_needs. The create_meal tool will retrieve consumed values from FatSecret separately.

If daily targets cannot be determined, ask the user for the missing information. Never substitute consumed values for daily targets.
"""
)

def main():
    messages =[]
    print("Nutrition Agent is ready! Type exit to quit <3.")
    while True:
        user_input = input("\nYou:> ").strip()
        if user_input.lower() == ("exit", "quit", "выход"):
            break
        if not user_input:
            continue

        messages.append({
            "role": "user",
            "content": user_input,
        })

        result = agent.invoke({"messages": messages})
        messages = result["messages"]

        print("\nAgent: ", messages[-1].content)

if __name__ == "__main__":
    main()

