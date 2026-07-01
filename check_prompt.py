from app.core.config import settings

def test():
    prompt = settings.get_template_script_prompt()
    print("----- PROMPT CARGADO -----")
    print(prompt)
    print("--------------------------")
    
    # Simulate what openai.py does
    system_prompt = prompt if prompt is not None else settings.get_grok_system_prompt()
    system_prompt = system_prompt.replace("{{dynamic_context}}", "")
    
    print("----- PROMPT FINAL -----")
    print(system_prompt)
    print("------------------------")

test()
