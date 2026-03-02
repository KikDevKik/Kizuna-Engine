with open('./backend/app/services/gemini_live.py', 'r') as f:
    content = f.read()

old_block = """            # Configure the session
            speech_config = None
            if voice_name:
                speech_config = types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )


            # Response modalities is set to AUDIO to ensure we get audio back.
            config = types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
                system_instruction=types.Content(
                    parts=[types.Part(text=system_instruction)]
                ),
                tools=[]
            )"""

new_block = """            # Configure the session
            config_params = {
                "response_modalities": ["AUDIO"],
                "system_instruction": types.Content(
                    parts=[types.Part(text=system_instruction)]
                ),
                "tools": []
            }

            if voice_name:
                config_params["speech_config"] = types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )

            config = types.LiveConnectConfig(**config_params)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('./backend/app/services/gemini_live.py', 'w') as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Block not found")
