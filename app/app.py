import streamlit as st
import pandas as pd
import re
import google.generativeai as genai

def create_elaborate_prompt(user_request):
    return f"""
You are an expert hobby advisor specializing in fitness and running. Your task is to create a detailed, data-driven analysis and recommendation plan for someone interested in taking up running as a hobby.

Here's the user request: {user_request}

Please structure your response in the following way:

1. Initial Assessment
- Analyze why running is a good hobby choice
- List the primary benefits (physical, mental, social)
- Identify potential challenges for beginners

2. Getting Started Plan
- Required equipment and estimated costs
- Recommended schedule for beginners
- Safety considerations and prerequisites

3. Progression Timeline
- Week-by-week breakdown for the first 8 weeks
- Monthly milestones for the first 6 months
- Long-term goals and achievements

4. Data Analysis
Please include data tables in your analysis with the following structure:

Equipment Costs:
| Item | Essential | Average Cost | Lifetime (Months) |
|------|-----------|--------------|-------------------|

Weekly Progress:
| Week | Running Minutes | Walking Minutes | Total Distance (Km) | Sessions Per Week |
|------|----------------|-----------------|-------------------|------------------|

Monthly Milestones:
| Month | Distance Goal (Km) | Avg Pace (Min/Km) | Long Run (Km) |
|-------|-------------------|-------------------|----------------|

5. Visualization Suggestions
- Weekly distance progression
- Pace improvements
- Heart rate zones
- Recovery metrics

6. Community and Support
- Recommended apps and tools
- Local groups or communities
- Online resources

7. Risk Analysis
Include a risk assessment matrix for common challenges and solutions.

Please provide a comprehensive response in a clear, structured manner with specific, actionable recommendations.
"""

def extract_tables(text):
    """Extract markdown tables from text"""
    table_pattern = r"\|.*?\|[\r\n][-|:\s]+[\r\n](?:\|.*?\|[\r\n])+"
    tables = []
    
    for table_match in re.finditer(table_pattern, text, re.MULTILINE):
        table_text = table_match.group(0)
        try:
            lines = [line.strip() for line in table_text.split('\n') if line.strip()]
            headers = [col.strip() for col in lines[0].split('|')[1:-1]]
            data = []
            for line in lines[2:]:
                row = [cell.strip() for cell in line.split('|')[1:-1]]
                data.append(row)
            df = pd.DataFrame(data, columns=headers)
            tables.append(df)
        except Exception as e:
            st.error(f"Error parsing table: {e}")
    return tables

def extract_sections(text):
    """Extract sections based on numbered points or headers"""
    sections = {}
    current_section = None
    current_content = []
    
    for line in text.split('\n'):
        # Check for section headers (numbered points or markdown headers)
        if re.match(r'^\d+\.|\#\#?|^\*\*', line.strip()):
            if current_section and current_content:  # Only save if there's content
                content = '\n'.join(current_content).strip()
                if content:  # Only save if content is not empty
                    sections[current_section] = content
            current_section = line.strip('*# \n')
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Add the last section if it has content
    if current_section and current_content:
        content = '\n'.join(current_content).strip()
        if content:
            sections[current_section] = content
    
    return sections

def main():
    st.title("AI Response Comparison: Simple vs. Elaborated Prompts")
    
    # Initialize Gemini (API key input)
    api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            st.error(f"Error configuring Gemini: {e}")
            return
    
    # User input
    user_request = st.text_area("Enter your request:", 
                               """I would like to learn running. Give me recommendations for 
                               this hobby with detailed analysis.""")
    
    if st.button("Generate Responses"):
        if not api_key:
            st.warning("Please enter your Gemini API key in the sidebar first.")
            return
            
        with st.spinner("Generating responses..."):
            # Create tabs for simple and elaborate responses
            simple_tab, elaborate_tab = st.tabs(["Simple Prompt", "Elaborated Prompt"])
            
            # Generate simple response
            with simple_tab:
                try:
                    simple_response = model.generate_content(user_request).text
                    st.markdown("### Simple Prompt Response")
                    st.markdown(simple_response)
                    
                    # Extract and display any tables from simple response
                    simple_tables = extract_tables(simple_response)
                    if simple_tables:
                        st.markdown("### Tables Found in Simple Response")
                        for i, table in enumerate(simple_tables):
                            if not table.empty:  # Only show non-empty tables
                                st.markdown(f"**Table {i+1}**")
                                st.dataframe(table)
                except Exception as e:
                    st.error(f"Error generating simple response: {e}")
            
            # Generate elaborate response
            with elaborate_tab:
                try:
                    elaborate_prompt = create_elaborate_prompt(user_request)
                    elaborate_response = model.generate_content(elaborate_prompt).text
                    
                    # Extract and display sections
                    sections = extract_sections(elaborate_response)
                    if sections:  # Only show sections header if there are sections
                        st.markdown("### Elaborated Response (Structured)")
                        for section_title, content in sections.items():
                            # Only create expander if content exists and is not just whitespace
                            if content and not content.isspace():
                                with st.expander(section_title):
                                    st.markdown(content)
                    
                    # Extract and display tables
                    elaborate_tables = extract_tables(elaborate_response)
                    if elaborate_tables:
                        st.markdown("### Tables Found in Elaborated Response")
                        for i, table in enumerate(elaborate_tables):
                            if not table.empty:  # Only show non-empty tables
                                st.markdown(f"**Table {i+1}**")
                                st.dataframe(table)
                            
                except Exception as e:
                    st.error(f"Error generating elaborate response: {e}")

if __name__ == "__main__":
    main()