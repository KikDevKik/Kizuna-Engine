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

export type ServerMessage = AudioMessage | TextMessage | TurnCompleteMessage;
