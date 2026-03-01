import re

with open('backend/app/services/audio_session.py', 'r') as f:
    content = f.read()

# 1. Add AUDIO_BUFFER_THRESHOLD constant
if "AUDIO_BUFFER_THRESHOLD" not in content:
    content = content.replace('async def send_to_gemini', 'AUDIO_BUFFER_THRESHOLD = 2048\n\nasync def send_to_gemini')

# 2. Remove Phase 7.0.3 Adaptive Noise Gate and auction_service.interrupt()
search_block = """                # 🏰 BASTION: RMS Energy Gate
                import math
                import struct
                count = len(data) // 2
                if count > 0:
                    sum_sq = 0
                    for i in range(0, len(data), 20):
                        try:
                            sample = struct.unpack_from('<h', data, i)[0]
                            sum_sq += sample * sample
                        except: break
                    rms = math.sqrt(sum_sq / (count / 10)) if count > 0 else 0

                    # Phase 7.0.3: Adaptive VAD Algorithm
                    dynamic_threshold = current_noise_floor + 1500.0

                    if rms > dynamic_threshold:
                        # The user is actually speaking
                        await auction_service.interrupt()
                    else:
                        # The user is silent. Slowly adapt the noise floor to ambient room changes.
                        # Using an Exponential Moving Average (EMA) to prevent sudden spikes from ruining the floor.
                        current_noise_floor = (0.95 * current_noise_floor) + (0.05 * rms)"""

if search_block in content:
    content = content.replace(search_block, "")

# 3. Fix turn aborted logic in receive_from_gemini
old_bid_logic = """                                won = await auction_service.bid(agent_id, 1.0)
                                if not won:
                                    logger.info(f"🔇 {agent_name} lost auction. Aborting TURN.")
                                    turn_aborted = True
                                    continue"""
new_bid_logic = """                                won = await auction_service.bid(agent_id, 1.0)
                                if not won:
                                    if auction_service._current_winner is not None:
                                        logger.info(f"🔇 {agent_name} lost auction due to conflict. Aborting TURN.")
                                        turn_aborted = True
                                    continue"""
if old_bid_logic in content:
    content = content.replace(old_bid_logic, new_bid_logic)

with open('backend/app/services/audio_session.py', 'w') as f:
    f.write(content)
