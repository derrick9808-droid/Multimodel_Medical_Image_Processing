/**
 * AudioEngine - Web Audio API Synthesizer for Drone Simulator
 * Provides real-time synthesized rotor audio, servo winch effects, clicks, and fanfares.
 */
class SoundEngine {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
    this.motorOsc1 = null;
    this.motorOsc2 = null;
    this.motorGain = null;
    this.motorFilter = null;
    this.isMotorRunning = false;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    if (this.motorGain) {
      this.motorGain.gain.setValueAtTime(this.isMuted ? 0 : 0.08, this.ctx.currentTime);
    }
    return this.isMuted;
  }

  startMotor() {
    if (this.isMotorRunning || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      // Dual oscillator for rich brushless motor harmonics
      this.motorOsc1 = this.ctx.createOscillator();
      this.motorOsc2 = this.ctx.createOscillator();
      this.motorGain = this.ctx.createGain();
      this.motorFilter = this.ctx.createBiquadFilter();

      this.motorOsc1.type = 'sawtooth';
      this.motorOsc2.type = 'triangle';

      this.motorOsc1.frequency.setValueAtTime(85, now);
      this.motorOsc2.frequency.setValueAtTime(170, now);

      this.motorFilter.type = 'lowpass';
      this.motorFilter.frequency.setValueAtTime(320, now);
      this.motorFilter.Q.setValueAtTime(2.5, now);

      this.motorGain.gain.setValueAtTime(0, now);
      this.motorGain.gain.linearRampToValueAtTime(this.isMuted ? 0 : 0.08, now + 0.6);

      this.motorOsc1.connect(this.motorFilter);
      this.motorOsc2.connect(this.motorFilter);
      this.motorFilter.connect(this.motorGain);
      this.motorGain.connect(this.ctx.destination);

      this.motorOsc1.start();
      this.motorOsc2.start();
      this.isMotorRunning = true;
    } catch (e) {
      console.warn("Audio motor start failed:", e);
    }
  }

  updateMotorThrottle(speedRatio, altitudeChange) {
    if (!this.isMotorRunning || !this.ctx || this.isMuted) return;
    const now = this.ctx.currentTime;
    // Map speed ratio (0 to 1) and climb rate to frequency
    const climbBoost = Math.max(-20, Math.min(40, altitudeChange * 30));
    const baseFreq = 85 + speedRatio * 90 + climbBoost;
    
    this.motorOsc1.frequency.setTargetAtTime(baseFreq, now, 0.08);
    this.motorOsc2.frequency.setTargetAtTime(baseFreq * 2.02, now, 0.08);
    this.motorFilter.frequency.setTargetAtTime(320 + speedRatio * 380, now, 0.1);
    this.motorGain.gain.setTargetAtTime(0.06 + speedRatio * 0.04, now, 0.1);
  }

  stopMotor() {
    if (!this.isMotorRunning || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      this.motorGain.gain.linearRampToValueAtTime(0.0001, now + 0.5);
      setTimeout(() => {
        if (this.motorOsc1) {
          this.motorOsc1.stop();
          this.motorOsc1.disconnect();
          this.motorOsc1 = null;
        }
        if (this.motorOsc2) {
          this.motorOsc2.stop();
          this.motorOsc2.disconnect();
          this.motorOsc2 = null;
        }
        this.isMotorRunning = false;
      }, 500);
    } catch (e) {
      this.isMotorRunning = false;
    }
  }

  playWinch() {
    if (this.isMuted || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      osc.type = 'square';
      osc.frequency.setValueAtTime(240, now);
      osc.frequency.linearRampToValueAtTime(280, now + 0.4);

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(600, now);
      filter.Q.setValueAtTime(4.0, now);

      gain.gain.setValueAtTime(0.03, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.45);
    } catch (e) {}
  }

  playLatch() {
    if (this.isMuted || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      // High click sound for magnetic latch
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(140, now + 0.08);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.09);
    } catch (e) {}
  }

  playWaypoint() {
    if (this.isMuted || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(987.77, now); // B5

      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.15);
    } catch (e) {}
  }

  playDeliverySuccess() {
    if (this.isMuted || !this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const noteTime = now + idx * 0.12;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, noteTime);

        gain.gain.setValueAtTime(0, noteTime);
        gain.gain.linearRampToValueAtTime(0.1, noteTime + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, noteTime + (idx === 3 ? 0.8 : 0.35));

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(noteTime);
        osc.stop(noteTime + 0.85);
      });
    } catch (e) {}
  }
}

window.soundEngine = new SoundEngine();

