import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="healio-494416", location="us-central1")

model = GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Patient has fever and rash. Give triage priority Red Yellow or Green with brief explanation.")
print(response.text)