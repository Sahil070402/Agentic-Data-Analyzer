import pandas as pd
import json
from autogen_agentchat.agents import AssistantAgent

class QueryClarityAgent:
    """
    Agent that generates contextual query suggestions for any user query.
    """
    
    def __init__(self, model_client, name="Query_Suggestions_Agent"):
        self.model_client = model_client
        self.agent = AssistantAgent(
            name=name,
            model_client=model_client,
            description="An agent that generates contextual suggestions for data analysis queries",
            system_message="""You are a Query Suggestions Agent. Your job is to:

1. Analyze user queries about data analysis and ALWAYS provide 5 similar query suggestions.
2. Generate suggestions that are closely related to the user's original query intent.
3. Use the ACTUAL column names from the CSV data to make suggestions specific and actionable.
4. Keep the suggestions similar to what the user asked but with proper column references.

SUGGESTION GUIDELINES:
- Stay close to the user's original query intent and wording
- Replace generic terms with actual column names from the CSV
- Maintain the same type of analysis the user seems to want
- Make suggestions that are variations or refinements of the original query
- Use actual column names to make queries more specific and executable

EXAMPLES:
User query: "what is date talking about this quarter" with columns [date, quarter, revenue, product, region]
Generate similar queries using actual column names:
- "What does the 'date' column show for this quarter?"
- "Show me data from the 'date' and 'quarter' columns"
- "What information is in the 'date' column for the current quarter?"
- "Display the 'date' values filtered by 'quarter'"
- "Analyze the 'date' column data for this quarter period"

User query: "show sales trends" with columns [sales, month, region, product]
Generate similar queries using actual column names:
- "Show 'sales' trends over 'month'"
- "Display 'sales' trends by 'region'"
- "Show 'sales' trends for each 'product'"
- "Create a trend chart of 'sales' by 'month'"
- "Analyze 'sales' trends across different 'region' values"

User query: "revenue analysis" with columns [revenue, date, customer, category]
Generate similar queries using actual column names:
- "Analyze 'revenue' by 'date'"
- "Show 'revenue' analysis by 'customer'"
- "Analyze 'revenue' trends across 'category'"
- "Display 'revenue' analysis over time using 'date'"
- "Compare 'revenue' performance by 'customer' and 'category'"

RESPONSE FORMAT:
ALWAYS respond with JSON containing suggestions:
{
    "suggestions": [
        "Similar query 1 using actual column names",
        "Similar query 2 using actual column names", 
        "Similar query 3 using actual column names",
        "Similar query 4 using actual column names",
        "Similar query 5 using actual column names"
    ]
}
"""
        )
    
    async def generate_query_suggestions(self, query: str, csv_info: dict) -> dict:
        """
        Generate contextual query suggestions based on user query and CSV data.
        
        Args:
            query: User's query string
            csv_info: Dictionary containing CSV metadata (columns, sample_data, shape)
            
        Returns:
            Dictionary with suggestions
        """
        
        # Prepare context about the CSV data
        context = f"""
AVAILABLE DATA COLUMNS: {csv_info['columns']}
DATA SHAPE: {csv_info['shape'][0]} rows, {csv_info['shape'][1]} columns

SAMPLE DATA:
{csv_info['sample_data']}

USER QUERY: "{query}"

Generate 5 similar query suggestions that are closely related to the user's original query. Use the ACTUAL column names from the CSV data to make the suggestions specific and actionable. Keep the suggestions similar to what the user asked but with proper column references.
"""
        
        try:
            # Use the AssistantAgent's run method to get response
            result = await self.agent.run(task=context)
            
            # Extract the response content from the result messages
            if result.messages:
                response_text = result.messages[-1].content.strip()
                
                # Clean up response if it has markdown formatting
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                parsed_result = json.loads(response_text)
                return parsed_result
            else:
                # If no messages, return error indication
                return {
                    "suggestions": [],
                    "error": "No response from suggestions agent"
                }
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return error indication
            return {
                "suggestions": [],
                "error": f"Unable to parse suggestions: {str(e)}"
            }
        except Exception as e:
            # For any other errors, return error indication
            return {
                "suggestions": [],
                "error": f"Error generating suggestions: {str(e)}"
            }

    async def evaluate_query_clarity(self, query: str, csv_info: dict) -> dict:
        """
        Evaluate query clarity and provide suggestions. 
        This method provides compatibility with the streamlit interface.
        
        Args:
            query: User's query string
            csv_info: Dictionary containing CSV metadata (columns, sample_data, shape)
            
        Returns:
            Dictionary with clarity evaluation and suggestions
        """
        
        # For now, we'll always show suggestions (not doing vague/clear evaluation)
        # This simplifies the user experience and always provides helpful suggestions
        suggestions_result = await self.generate_query_suggestions(query, csv_info)
        
        if "error" in suggestions_result:
            # If there was an error generating suggestions, consider query clear
            return {
                "is_clear": True,
                "reason": "Unable to generate suggestions, proceeding with analysis"
            }
        else:
            # Always show suggestions to help users refine their queries
            return {
                "is_clear": False,  # Always show suggestions for better user experience
                "reason": "Here are some related query suggestions to help you get better results",
                "clarifying_questions": suggestions_result.get("suggestions", [])
            }

def get_csv_info(file_path: str) -> dict:
    """
    Extract relevant information from CSV file for query suggestions.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary with CSV metadata
    """
    try:
        df = pd.read_csv(file_path)
        
        # Get basic info
        csv_info = {
            'columns': df.columns.tolist(),
            'shape': df.shape,
            'sample_data': df.head(3).to_string(index=False)
        }
        
        return csv_info
        
    except Exception as e:
        return {
            'columns': [],
            'shape': (0, 0),
            'sample_data': f"Error reading CSV: {str(e)}"
        }

def create_query_clarity_agent(model_client):
    """
    Factory function to create a Query Suggestions Agent.
    
    Args:
        model_client: OpenAI model client
        
    Returns:
        QueryClarityAgent instance
    """
    return QueryClarityAgent(model_client)
