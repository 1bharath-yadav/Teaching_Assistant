import { getClientConfig } from "../../config/client";
import { TDS_API_BASE_URL, TDS_API_ENDPOINT } from "../../constant";
import { 
  LLMApi, 
  ChatOptions, 
  LLMUsage, 
  LLMModel, 
  RequestMessage,
  SpeechOptions,
  LLMConfig
} from "../api";

export interface TDSApiRequestPayload {
  question: string;
  image?: string; // base64-encoded image
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
}

export interface TDSApiResponse {
  answer: string;
  sources?: string[];
  links?: Array<{
    url: string;
    text: string;
  }>;
}

export class TDSApi implements LLMApi {
  private baseUrl: string;

  constructor() {
    this.baseUrl = TDS_API_BASE_URL;
  }

  async chat(options: ChatOptions): Promise<void> {
    const { messages, config, onUpdate, onFinish, onError, onController } = options;
    
    try {
      const controller = new AbortController();
      onController?.(controller);

      const payload = this.convertMessagesToTDSPayload(messages, config);
      const response = await this.sendTDSRequest(payload, controller);
      
      const formattedResponse = this.convertTDSResponseToMessages(response);
      
      // Simulate streaming by calling onUpdate and then onFinish
      onUpdate?.(formattedResponse, formattedResponse);
      onFinish(formattedResponse, new Response(JSON.stringify(response)));
      
    } catch (error) {
      console.error("TDS API chat error:", error);
      onError?.(error as Error);
    }
  }

  async speech(options: SpeechOptions): Promise<ArrayBuffer> {
    throw new Error("Speech functionality not supported by TDS API");
  }

  async usage(): Promise<LLMUsage> {
    // Return mock usage data since TDS API doesn't track usage
    return {
      used: 0,
      total: Infinity,
    };
  }

  async models(): Promise<LLMModel[]> {
    return [
      {
        name: "tds-assistant",
        displayName: "TDS Teaching Assistant",
        available: true,
        provider: {
          id: "tds",
          providerName: "TDS Assistant",
          providerType: "custom",
          sorted: 1,
        },
        sorted: 1,
      },
    ];
  }

  private async sendTDSRequest(
    payload: TDSApiRequestPayload, 
    controller?: AbortController
  ): Promise<TDSApiResponse> {
    const url = `${this.baseUrl}${TDS_API_ENDPOINT}`;
    
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller?.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`TDS API Error: ${response.status} ${errorText}`);
    }

    const data: TDSApiResponse = await response.json();
    return data;
  }

  // Convert NextChat message format to TDS API format
  convertMessagesToTDSPayload(messages: RequestMessage[], config: LLMConfig): TDSApiRequestPayload {
    // Get the last user message as the question
    const userMessages = messages.filter(msg => msg.role === "user");
    const lastUserMessage = userMessages[userMessages.length - 1];
    
    if (!lastUserMessage) {
      throw new Error("No user message found");
    }

    let question = "";
    let image: string | undefined;

    // Handle multimodal content
    if (typeof lastUserMessage.content === "string") {
      question = lastUserMessage.content;
    } else if (Array.isArray(lastUserMessage.content)) {
      // Extract text and image from multimodal content
      const textParts = lastUserMessage.content
        .filter(part => part.type === "text")
        .map(part => part.text)
        .filter(Boolean);
      
      const imageParts = lastUserMessage.content
        .filter(part => part.type === "image_url")
        .map(part => part.image_url?.url)
        .filter(Boolean);

      question = textParts.join(" ");
      
      if (imageParts.length > 0) {
        // Extract base64 data from data URL
        const imageUrl = imageParts[0];
        if (imageUrl?.startsWith("data:")) {
          const base64Data = imageUrl.split(",")[1];
          image = base64Data;
        }
      }
    }

    return {
      question: question || "Please help me with my question.",
      image,
      temperature: config.temperature,
      max_tokens: config.max_tokens,
      top_p: config.top_p,
      presence_penalty: config.presence_penalty,
      frequency_penalty: config.frequency_penalty,
    };
  }

  // Convert TDS API response to NextChat format
  convertTDSResponseToMessages(response: TDSApiResponse): string {
    let answer = response.answer;
    
    // Append sources/links if available
    if (response.links && response.links.length > 0) {
      answer += "\n\n**Sources:**\n";
      response.links.forEach((link, index) => {
        answer += `${index + 1}. [${link.text}](${link.url})\n`;
      });
    } else if (response.sources && response.sources.length > 0) {
      answer += "\n\n**Sources:**\n";
      response.sources.forEach((source, index) => {
        answer += `${index + 1}. ${source}\n`;
      });
    }

    return answer;
  }
}
