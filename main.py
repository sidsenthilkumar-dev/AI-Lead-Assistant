from google import genai

# Connect to Gemini
client = genai.Client()

# Example customer lead
lead = """
Hi, I'm interested in getting a quote for replacing my roof.
My roof is about 15 years old and has started leaking.
I'm located in Apex, NC and would like someone to come take a look.
"""

# Tell the AI what we want it to do with the lead
prompt = f"""
You are an AI assistant that helps businesses manage customer leads.

Analyze the following customer lead:

{lead}

Give me:

1. The type of service the customer needs
2. How urgent the lead appears
3. What information the business already knows
4. What information is missing
5. A professional response the business could send to the customer
"""

# Send the lead to Gemini
response = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt
)

# Print the AI's response
print(response.output_text)
