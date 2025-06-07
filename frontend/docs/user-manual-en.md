# TDS Assistant User Manual

This document explains the features and design principles of the TDS (Tools in Data Science) Assistant for IIT Madras Online Degree Program.

## Introduction to TDS Assistant

The TDS Assistant is specially designed for students of the IIT Madras Online Degree Program, particularly for the Tools in Data Science course. It helps students with:

- Answering questions about data science tools and techniques
- Providing guidance on course assignments and projects
- Offering explanations on complex data science concepts
- Assisting with code-related queries
- Finding relevant course materials and resources

This AI assistant uses Retrieval-Augmented Generation (RAG) to access course-specific knowledge and provide accurate, contextual responses tailored to the IITM curriculum.

## Masks (Personas)

### What are Masks? What's the difference between masks and prompts?

Mask = Multiple preset prompts + Model settings + Conversation settings.

Preset prompts (Contextual Prompts) are generally used for In-Context Learning to help generate outputs that better meet requirements. They can also add system constraints or input limited additional knowledge.

Model settings are self-explanatory; conversations created with a specific mask will use the corresponding model parameters by default.

Conversation settings include a series of configurations related to the conversation experience, which we'll explain in the following sections.

### How to add a preset mask?

Currently, preset masks can only be added by editing the source code. Edit the corresponding language file in the [mask](../app/masks/) directory as needed.

Follow these steps:

1. Configure a mask in TDS Assistant
2. Use the download button on the mask editing page to save the mask in JSON format
3. Format the JSON file into corresponding TypeScript code
4. Place it in the appropriate .ts file

Support for side-loading masks will be added in future updates.

## Conversations

### Functions of the buttons above the conversation box

In the default state, hover over a button to see its text description. We'll introduce them in order:

- Conversation Settings: Settings for the current conversation; for their relationship with global settings, see the next section
- Color Theme: Click to cycle between automatic, dark, and light modes
- Quick Commands: Built-in shortcuts to fill in preset prompts; you can also type / in the conversation box to search
- All Masks: Enter the masks page
- Clear Chat: Insert a clear marker; chats above the marker won't be sent to GPT. This effectively clears the current conversation. You can click this button again to cancel clearing
- Model Settings: Change the model for the current conversation. Note that this button only modifies the model for the current conversation, not the global default model

### Relationship between conversation settings and global settings

There are currently two settings entry points:

1. The settings button in the bottom left corner of the page, which leads to global settings
2. The settings button above the conversation box, which leads to conversation settings

After creating a new conversation, its settings synchronize with global settings by default. When you modify global settings, the conversation settings of newly created conversations will also be synchronized.

Once a user manually changes conversation settings, they will no longer synchronize with global settings. Changes to global settings will not affect this conversation.

To restore synchronization, check the "Use Global Settings" option in the conversation settings.

### Meaning of conversation settings items

Open the button above the conversation box to access conversation settings. From top to bottom, the contents are:

- Preset prompt list: Add, delete, or sort preset prompts
- Character avatar: Self-explanatory
- Character name: Self-explanatory
- Hide preset conversation: When hidden, preset prompts won't appear in the chat interface
- Use global settings: Indicates whether the current conversation uses global conversation settings
- Model setting options: The remaining options have the same meaning as global settings, see the next section

### Meaning of global settings items

- model / temperature / top_p / max_tokens / presence_penalty / frequency_penalty are all ChatGPT setting parameters. For details, please refer to the official OpenAI documentation
- Inject system-level prompt information, User input preprocessing: For details, see [this link](https://github.com/Yidadaa/ChatGPT-Next-Web/issues/2144)
- Include message history count: The number of recent messages carried when a user inputs and sends a message
- Message length compression threshold: When the chat reaches this character count, the history summary function automatically triggers
- Message history summary: Whether to enable the history summary function

### What is message history summary?

The message history summary function, also known as history compression, is key to maintaining historical memory in long conversations. Proper use of this feature can save tokens while preserving historical topic information.

Due to ChatGPT API length limitations (for example, the 3.5 model can only accept conversations less than 4096 tokens), errors occur when exceeding this value.

To help ChatGPT understand our conversation context, we often include multiple historical messages, which can easily trigger length limitations after conversing for a while.

To solve this problem, we added the history compression feature. If the threshold is set to 1000 characters, whenever user-generated chat records exceed 1000 characters, messages that haven't been summarized will be sent to ChatGPT to generate a summary of about 100 characters.

This compresses 1000 characters of historical information to 100 characters. It's a lossy compression but satisfies most use cases.

### When should I turn off message history summary?

History summary may affect ChatGPT's conversation quality, so if the conversation scenario is translation, information extraction, or other one-time conversation scenarios, please disable the history summary function and set the message history count to 0.

### What information is sent when a user sends a message?

When a user enters a message in the conversation box, the message sent to ChatGPT includes:

1. System-level prompt: Used to match the official ChatGPT WebUI experience as closely as possible; can be disabled in settings
2. History summary: Acts as long-term memory, providing long-lasting but fuzzy context information
3. Preset prompts: Preset prompts set in the current conversation settings, used for In-Context Learning or injecting system-level constraints
4. Recent conversation records: Acts as short-term memory, providing brief but precise context information
5. The user's current input message
