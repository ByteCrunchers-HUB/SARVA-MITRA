from backend.rag_pipeline.rag import RAGPipeline

def test_rag_modes_init():
    rag = RAGPipeline()
    assert hasattr(rag, "master_prompt")
    assert hasattr(rag, "chat_prompt")
    assert "Directly address and answer the farmer's specific question" in rag.chat_prompt
    assert "Suggested Follow-Up Questions" in rag.chat_prompt
    print("RAGPipeline initialized with dual prompts: PASS")

if __name__ == "__main__":
    test_rag_modes_init()
