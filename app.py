from src import create_app

# Create the application instance using the factory
app = create_app()

if __name__ == '__main__':
    # The host must be set to '0.0.0.0' to be accessible from outside the container
    # if you are using Docker
    app.run(host='127.0.0.1', port=5001, debug=True)
    
    
    from openai import OpenAI
client = OpenAI()

models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]

for model in models:
  response = client.responses.create(
      model=model,
      input="Write a one-sentence bedtime story about a unicorn."
  )

  print(response.output_text)
