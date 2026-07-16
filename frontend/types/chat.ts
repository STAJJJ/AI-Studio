export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

export type ChatRoleInfo = {
  id: string;
  name: string;
  description: string;
};

export type ChatRolesResponse = {
  roles: ChatRoleInfo[];
};

export type ChatStreamEvent =
  | {
      type: "delta";
      content: string;
    }
  | {
      type: "error";
      message: string;
    }
  | {
      type: "done";
    };

export type ChatCompletionRequest = {
  role_id: string;
  model: string;
  messages: ChatMessage[];
  temperature: number;
  max_tokens: number;
  stream: true;
};
