def clean_input(prompt: str='', hint: str="GPT"):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print(f"You interrupted Auto-{hint}")
        print("Quitting...")
        exit(0)

