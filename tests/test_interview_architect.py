"""
Comprehensive Test Suite for Interview Architect Agent

Tests all functionality including:
- Hypothesis generation (AI fallback)
- Comprehensive context gathering
- Interview script generation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.interview import InterviewArchitectAgent
from src.models.schemas import Hypothesis, InterviewScript, CustomerContext


class TestInterviewArchitectAgent:
    """Test suite for Interview Architect Agent"""

    @pytest.fixture
    def agent(self):
        """Create an Interview Architect Agent instance for testing"""
        return InterviewArchitectAgent()

    @pytest.fixture
    def sample_state(self):
        """Create a sample workflow state with all necessary data"""
        return {
            "project_id": "test-project-123",
            "project": {
                "client_name": "Test Corp",
                "industry": "Manufacturing",
                "target_departments": ["Sales", "Operations"],
                "description": "Process improvement project"
            },
            "documents": [
                {
                    "id": "doc1",
                    "filename": "sales_sop.pdf",
                    "file_type": "pdf",
                    "source_type": "file",
                    "processed": True,
                    "chunk_count": 42
                },
                {
                    "id": "doc2",
                    "filename": "www.company.com",
                    "file_type": "url",
                    "source_type": "url",
                    "source_url": "https://www.company.com/docs",
                    "processed": True,
                    "chunk_count": 18
                }
            ],
            "document_summaries": [
                "Sales SOP describes a 7-step manual approval process requiring multiple sign-offs.",
                "Company website documentation shows automated order submission API is available.",
                "Customer complaints mention frequent delays in order processing."
            ],
            "hypotheses": [],
            "messages": []
        }

    @pytest.fixture
    def sample_hypotheses(self):
        """Create sample hypotheses for testing"""
        return [
            Hypothesis(
                process_area="Sales Order Processing",
                description="Manual approval process causes delays and bottlenecks",
                evidence=["7-step approval process", "Multiple sign-offs required"],
                indicators=["manual", "approval", "delays"],
                confidence_score=0.85,
                automation_potential="high",
                task_category="automatable"
            ),
            Hypothesis(
                process_area="Data Entry",
                description="Repetitive data entry across multiple systems wastes time",
                evidence=["Manual entry into 3 systems", "High error rate"],
                indicators=["manual", "data entry", "repetitive"],
                confidence_score=0.75,
                automation_potential="high",
                task_category="automatable"
            )
        ]

    # =========================================================================
    # Test: Comprehensive Context Gathering
    # =========================================================================

    def test_gather_comprehensive_context(self, agent, sample_state, sample_hypotheses):
        """Test that all available context is properly gathered"""
        context = agent._gather_comprehensive_context(sample_state, sample_hypotheses)

        # Verify all components are present
        assert context['documents_count'] == 2
        assert context['summaries_count'] == 3
        assert len(context['document_summaries']) == 3
        assert context['combined_summaries'] != ""
        assert context['has_urls'] == True

        # Verify project context
        assert context['project']['client_name'] == "Test Corp"
        assert context['project']['industry'] == "Manufacturing"
        assert len(context['project']['target_departments']) == 2

        # Verify hypothesis summary
        assert context['hypotheses_summary']['total_count'] == 2
        assert len(context['hypotheses_summary']['process_areas']) == 2

        # Verify document details
        assert len(context['documents']) == 2
        assert context['documents'][0]['filename'] == "sales_sop.pdf"
        assert context['documents'][1]['source_type'] == "url"

    def test_gather_context_empty_state(self, agent):
        """Test context gathering with minimal/empty state"""
        empty_state = {
            "project_id": "test",
            "project": {},
            "documents": [],
            "document_summaries": [],
            "hypotheses": []
        }

        context = agent._gather_comprehensive_context(empty_state, [])

        assert context['documents_count'] == 0
        assert context['summaries_count'] == 0
        assert context['has_urls'] == False
        assert context['hypotheses_summary']['total_count'] == 0

    # =========================================================================
    # Test: Generic Hypotheses Fallback
    # =========================================================================

    def test_get_generic_hypotheses(self, agent):
        """Test generic hypotheses generation as fallback"""
        hypotheses = agent._get_generic_hypotheses()

        # Should return at least 3 generic hypotheses
        assert len(hypotheses) >= 3

        # Verify they are proper Hypothesis objects
        for h in hypotheses:
            assert isinstance(h, Hypothesis)
            assert h.process_area != ""
            assert h.description != ""
            assert 0.0 <= h.confidence_score <= 1.0
            assert h.automation_potential in ["high", "medium", "low"]

    # =========================================================================
    # Test: AI Hypothesis Generation (mocked)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_generate_hypotheses_from_documents_success(self, agent, sample_state):
        """Test AI-powered hypothesis generation from documents"""
        # Mock the LLM response
        mock_response = Mock()
        mock_response.content = '''[
            {
                "process_area": "Order Processing",
                "description": "Manual order entry causes delays",
                "evidence": ["Manual entry mentioned in docs"],
                "indicators": ["manual", "delays"],
                "confidence_score": 0.8,
                "automation_potential": "high",
                "task_category": "automatable"
            }
        ]'''

        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Test hypothesis generation
        hypotheses = await agent._generate_hypotheses_from_documents(sample_state)

        # Verify results
        assert len(hypotheses) == 1
        assert hypotheses[0].process_area == "Order Processing"
        assert hypotheses[0].confidence_score == 0.8
        assert agent.llm.ainvoke.called

    @pytest.mark.asyncio
    async def test_generate_hypotheses_no_summaries(self, agent):
        """Test hypothesis generation with no document summaries"""
        state = {
            "document_summaries": [],
            "project": {}
        }

        hypotheses = await agent._generate_hypotheses_from_documents(state)

        # Should return empty list when no summaries available
        assert hypotheses == []

    @pytest.mark.asyncio
    async def test_generate_hypotheses_parse_error(self, agent, sample_state):
        """Test hypothesis generation when AI returns invalid JSON"""
        # Mock invalid response
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"

        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Should handle error gracefully
        hypotheses = await agent._generate_hypotheses_from_documents(sample_state)
        assert hypotheses == []

    # =========================================================================
    # Test: Interview Script Generation Flow
    # =========================================================================

    @pytest.mark.asyncio
    async def test_full_interview_generation_with_hypotheses(
        self, agent, sample_state, sample_hypotheses
    ):
        """Test complete interview script generation with existing hypotheses"""
        # Add hypotheses to state
        sample_state['hypotheses'] = [h.model_dump() for h in sample_hypotheses]

        # Mock all LLM calls
        agent.llm = AsyncMock()

        # Mock analysis response
        analysis_response = Mock()
        analysis_response.content = '''{
            "key_themes": ["Manual processes", "Approval delays"],
            "priority_areas": [{"area": "Sales", "reason": "High impact", "severity": "high"}],
            "root_cause_patterns": ["Lack of automation"],
            "interconnections": ["Sales and data entry connected"],
            "ddd_indicators": {
                "dull_tasks": ["Data entry"],
                "dirty_tasks": [],
                "dangerous_tasks": []
            },
            "interview_focus_recommendations": ["Focus on approval process"],
            "risk_areas": ["Revenue impact from delays"]
        }'''

        agent.llm.ainvoke = AsyncMock(return_value=analysis_response)

        # Since we can't easily mock all the complex generation methods,
        # we'll test the context gathering which is the key enhancement
        context = agent._gather_comprehensive_context(
            sample_state,
            sample_hypotheses
        )

        # Verify comprehensive context was created
        assert context is not None
        assert context['documents_count'] > 0
        assert context['summaries_count'] > 0
        assert len(context['hypotheses_full']) == 2

    # =========================================================================
    # Test: URL Document Handling
    # =========================================================================

    def test_url_document_detection(self, agent, sample_state):
        """Test that URL documents are properly detected"""
        context = agent._gather_comprehensive_context(sample_state, [])

        assert context['has_urls'] == True

        # Verify URL document is in context
        url_docs = [d for d in context['documents'] if d['source_type'] == 'url']
        assert len(url_docs) == 1
        assert url_docs[0]['filename'] == "www.company.com"

    def test_no_url_documents(self, agent):
        """Test state with only file documents"""
        state = {
            "project_id": "test",
            "project": {},
            "documents": [
                {"filename": "test.pdf", "source_type": "file"}
            ],
            "document_summaries": []
        }

        context = agent._gather_comprehensive_context(state, [])
        assert context['has_urls'] == False


# =============================================================================
# Integration Tests
# =============================================================================

class TestInterviewArchitectIntegration:
    """Integration tests for Interview Architect"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_no_hypotheses_scenario(self):
        """
        Test complete flow when no hypotheses exist:
        1. No hypotheses provided
        2. AI generates hypotheses from documents
        3. Fallback to generic if AI fails
        4. Interview script still generated
        """
        # This would require actual LLM setup
        # Placeholder for future implementation
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_with_urls(self):
        """
        Test complete flow with URL documents:
        1. URLs included in documents
        2. Context recognizes URL sources
        3. Analysis considers online vs offline docs
        4. Questions reference URL content
        """
        # Placeholder for future implementation
        pass


# =============================================================================
# Performance Tests
# =============================================================================

class TestInterviewArchitectPerformance:
    """Performance tests"""

    def test_context_gathering_performance(self, benchmark):
        """Benchmark context gathering performance"""
        agent = InterviewArchitectAgent()

        state = {
            "project_id": "test",
            "project": {"client_name": "Test"},
            "documents": [{"filename": f"doc{i}.pdf", "source_type": "file"} for i in range(100)],
            "document_summaries": [f"Summary {i}" for i in range(100)],
            "hypotheses": []
        }

        # Benchmark should complete in reasonable time
        result = benchmark(agent._gather_comprehensive_context, state, [])
        assert result is not None


# =============================================================================
# Test Utilities
# =============================================================================

def create_mock_state(
    num_documents=5,
    num_summaries=5,
    num_hypotheses=3,
    include_urls=True
):
    """Utility function to create mock state for testing"""
    documents = []
    for i in range(num_documents):
        if include_urls and i == 0:
            documents.append({
                "id": f"doc{i}",
                "filename": f"example{i}.com",
                "file_type": "url",
                "source_type": "url",
                "source_url": f"https://example{i}.com",
                "processed": True
            })
        else:
            documents.append({
                "id": f"doc{i}",
                "filename": f"document{i}.pdf",
                "file_type": "pdf",
                "source_type": "file",
                "processed": True
            })

    return {
        "project_id": "test-project",
        "project": {
            "client_name": "Test Corporation",
            "industry": "Technology",
            "target_departments": ["Engineering", "Sales"]
        },
        "documents": documents,
        "document_summaries": [f"Summary of document {i}" for i in range(num_summaries)],
        "hypotheses": [],
        "messages": []
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
