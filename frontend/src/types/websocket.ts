export type AudioMessage = {
  type: 'audio';
  data: string;
};

export type TextMessage = {
  type: 'text';
  data: string;
};

export type TurnCompleteMessage = {
  type: 'turn_complete';
};

export type ControlMessage = {
  type: 'control';
  action: 'hangup';
  reason?: string;
};

export type SessionReadyMessage = {
  type: 'session_ready';
};

export type ActionMessage = {
  type: 'action';
  action: 'open_url';
  url: string;
};

export type ServerMessage = AudioMessage | TextMessage | TurnCompleteMessage | ControlMessage | SessionReadyMessage | ActionMessage;
