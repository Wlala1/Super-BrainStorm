# Super-BrainStorm
An intelligent brainstorming system powered by collaboration among multiple large language models. Through division of labor across Doubao, ChatGPT, and Gemini, it delivers new, useful and personalized idea generation for users.

✨ Key Features
	•	🤖 Multi-model Collaboration: Doubao generates ideas, ChatGPT refines solutions, Gemini evaluates and scores.
	•	👤 Personalization: Smart ranking based on user interests and history.
	•	🎯 High-quality Output: Multi-dimensional evaluation ensures relevance and feasibility.
	•	🏗️ Modular Design: Easily extensible and maintainable architecture.
	•	⚡ Production-grade Stability: Robust error handling and retry mechanisms.

Model Roles
	•	Doubao (DoubaoAdapter): Idea Generator — produces raw ideas from the topic and user profile.
	•	ChatGPT (ChatGPTAdapter): Plan Refiner — turns ideas into detailed, executable plans.
	•	Gemini (GeminiAdapter): Quality Evaluator — scores ideas across multiple dimensions and selects the best.

Scoring Dimensions
	1.	Topic Relevance (30%): Alignment with the original topic.
	2.	User Fit (20%): Personalization based on the user’s background.
	3.	Feasibility (25%): Practical operability of the plan.
	4.	Originality (25%): Uniqueness and creativity.
 
brainstorm_project/
├── config/                   # Configuration directory
│   ├── __init__.py           # Package initializer
│   ├── config.py             # Config class definitions
│   ├── .env.example          # Environment variable template
│   ├── requirements.txt      # Python dependencies
│   ├── schema.sql            # Database schema
│   └── setup.md              # Detailed deployment guide
├── model_adapters.py         # Three model adapters
├── user_profile.py           # User profile management
├── brainstorm_engine.py      # Core brainstorming engine
├── main_handler.py           # Main request handler
└── README.md                 # Project documentation
