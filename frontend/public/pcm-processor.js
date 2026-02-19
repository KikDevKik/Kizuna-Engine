class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.packetCount = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      const float32Data = input[0];
      this.packetCount++;
      const int16Data = this.float32ToInt16(float32Data);
      this.port.postMessage(int16Data, [int16Data.buffer]);
    }
    return true;
  }

  float32ToInt16(float32Data) {
    const int16Data = new Int16Array(float32Data.length);
    for (let i = 0; i < float32Data.length; i++) {
      let s = Math.max(-1, Math.min(1, float32Data[i]));
      int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Data;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
