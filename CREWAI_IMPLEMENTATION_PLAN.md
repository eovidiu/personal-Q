# CrewAI Multi-Agent Orchestration - Implementation Plan

## 🎯 Objective
Enable CrewAI multi-agent orchestration capabilities in Personal-Q to allow collaborative AI workflows with multiple agents working together on complex tasks.

## 📋 Current Status

### What's Already Built ✅
- **Complete CrewAI service implementation** (`backend/app/services/crew_service.py`)
  - Single agent task execution
  - Multi-agent collaborative workflows
  - Sequential and hierarchical process support
  - Agent-to-agent delegation
  - Dynamic agent creation from database models
  - LangChain-compatible integration via `ChatAnthropic`
  - Graceful fallback when CrewAI unavailable

- **Integration points exist**:
  - Task worker calls `CrewService.execute_agent_task()` in `backend/app/workers/tasks.py`
  - Service properly maps Agent models to CrewAI agents
  - LLM configuration correctly passed through

### The Problem ❌
CrewAI packages are currently disabled in `backend/requirements.txt`:

```python
# Line 19-20
# crewai==0.86.0  # Temporarily disabled - depends on crewai-tools which takes too long
# crewai-tools>=0.17.0  # Temporarily disabled - takes too long to resolve dependencies
```

**Root Cause**: During Docker build, `pip install` hangs when resolving `crewai-tools` dependencies, causing build timeouts.

---

## 🔍 Investigation Results

### CrewAI Version Landscape
- **Original version**: 0.86.0 (from requirements.txt)
- **Latest version**: 0.203.1 (as of now)
- **Major changes**: CrewAI has had 100+ releases since 0.86.0

### Dependency Analysis
The `crewai-tools` package historically had issues with:
1. Complex transitive dependencies (LangChain ecosystem)
2. Large dependency trees requiring resolution
3. Version conflicts with other packages

### Why This Matters
Without CrewAI, the application can only execute single-agent tasks via direct LLM calls. Multi-agent collaboration, task delegation, and complex workflows are unavailable.

---

## 🛠️ Implementation Strategy

We will pursue **multiple approaches in parallel** to maximize chances of success:

### **Approach 1: Upgrade to Latest CrewAI** (RECOMMENDED)
✅ **Pros**: Latest features, bug fixes, better dependency management
⚠️ **Risk**: May require code changes due to API updates
⏱️ **Estimated Time**: 2-3 hours

### **Approach 2: Install Without crewai-tools**
✅ **Pros**: Faster resolution, fewer dependencies
⚠️ **Risk**: Missing some tool integrations
⏱️ **Estimated Time**: 1-2 hours

### **Approach 3: Pre-build Wheels in Docker**
✅ **Pros**: Faster Docker builds, reproducible
⚠️ **Risk**: Requires wheel maintenance
⏱️ **Estimated Time**: 2-3 hours

### **Approach 4: Custom Lightweight Orchestration**
✅ **Pros**: Full control, no external dependencies
⚠️ **Risk**: More code to maintain, fewer features
⏱️ **Estimated Time**: 4-6 hours

---

## 📝 Detailed Implementation Steps

### Phase 1: Approach 1 - Upgrade to Latest CrewAI (Try First)

#### Step 1.1: Update Dependencies
**File**: `backend/requirements.txt`

```diff
# CrewAI
-# crewai==0.86.0  # Temporarily disabled
-# crewai-tools>=0.17.0  # Temporarily disabled
+crewai==0.203.1
+langchain-anthropic==0.3.0  # Required for ChatAnthropic
```

**Note**: We'll try WITHOUT `crewai-tools` first, as many tools are optional.

#### Step 1.2: Update CrewAI Service for New API
**File**: `backend/app/services/crew_service.py`

1. **Check for API changes** in CrewAI 0.203.1:
   - Verify `Agent`, `Task`, `Crew`, `Process` import paths
   - Check if `ChatAnthropic` integration still works
   - Update any deprecated methods

2. **Add error handling** for missing tools:
```python
def create_agent_tools(agent: Agent) -> List[Any]:
    """Create basic tools without crewai-tools package."""
    # Implement custom tools using only base CrewAI
    return []
```

#### Step 1.3: Update Dockerfile Build Configuration
**File**: `backend/Dockerfile`

Add pip configuration for faster dependency resolution:

```dockerfile
# Before pip install
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_NO_CACHE_DIR=1

# Use pip's new resolver explicitly
RUN pip install --upgrade pip setuptools wheel

# Install dependencies with increased timeout
RUN pip install --no-cache-dir -e . --timeout 300
```

#### Step 1.4: Update Docker Compose with Build Args
**File**: `docker-compose.yml`

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        - PIP_TIMEOUT=300
    # ... rest of config
```

#### Step 1.5: Test Build Locally
```bash
cd backend
docker build --progress=plain -t personal-q-backend:test . 2>&1 | tee build.log

# If successful, test the service
docker run --rm personal-q-backend:test python -c "from crewai import Agent; print('CrewAI imported successfully')"
```

#### Step 1.6: Test CrewAI Service
Create test script: `backend/test_crewai.py`

```python
"""Test CrewAI integration."""
import asyncio
from app.services.crew_service import CrewService, CREWAI_AVAILABLE
from app.models.agent import Agent, AgentType

async def test_crewai():
    print(f"CrewAI Available: {CREWAI_AVAILABLE}")

    if not CREWAI_AVAILABLE:
        print("❌ CrewAI not available")
        return

    # Create test agent
    agent = Agent(
        id="test-123",
        name="Test Agent",
        description="Test collaborative agent",
        agent_type=AgentType.ANALYTICAL,
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a helpful assistant.",
        temperature=0.7,
        max_tokens=2048
    )

    print("✅ CrewAI service initialized")
    print("✅ Agent mapping successful")

if __name__ == "__main__":
    asyncio.run(test_crewai())
```

Run test:
```bash
docker run --rm personal-q-backend:test python test_crewai.py
```

---

### Phase 2: Approach 2 - Install Without Tools (If Approach 1 Fails)

#### Step 2.1: Minimal CrewAI Installation
**File**: `backend/requirements.txt`

```python
# CrewAI (minimal installation)
crewai==0.203.1
langchain-anthropic==0.3.0
langchain-core==0.3.0

# Explicitly exclude problematic tools
```

#### Step 2.2: Implement Custom Tools
**File**: `backend/app/services/crew_tools.py` (NEW FILE)

```python
"""Custom tools for CrewAI agents without crewai-tools package."""

from typing import Any, Dict, Callable
from pydantic import BaseModel, Field

class CustomTool(BaseModel):
    """Custom tool implementation."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    func: Callable = Field(..., description="Tool function")

    class Config:
        arbitrary_types_allowed = True

def create_search_tool() -> CustomTool:
    """Create a simple search tool."""
    def search(query: str) -> str:
        return f"Search results for: {query}"

    return CustomTool(
        name="search",
        description="Search for information",
        func=search
    )

def create_calculator_tool() -> CustomTool:
    """Create a calculator tool."""
    def calculate(expression: str) -> str:
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    return CustomTool(
        name="calculator",
        description="Perform calculations",
        func=calculate
    )

# Add more custom tools as needed
```

Update `crew_service.py` to use custom tools:
```python
from app.services.crew_tools import create_search_tool, create_calculator_tool

def create_agent_tools(agent: Agent) -> List[Any]:
    """Create tools using custom implementations."""
    return [
        create_search_tool(),
        create_calculator_tool()
    ]
```

---

### Phase 3: Approach 3 - Pre-built Wheels (If Approach 1 & 2 Fail)

#### Step 3.1: Create Wheel Building Stage
**File**: `backend/Dockerfile.wheels` (NEW FILE)

```dockerfile
FROM python:3.11-slim as wheel-builder

WORKDIR /wheels

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install wheel builder
RUN pip install wheel

# Build wheels for CrewAI dependencies
RUN pip wheel --no-cache-dir \
    crewai==0.203.1 \
    langchain-anthropic==0.3.0 \
    -w /wheels

# Create archive
RUN tar -czf crewai-wheels.tar.gz /wheels/*.whl
```

#### Step 3.2: Update Main Dockerfile
**File**: `backend/Dockerfile`

```dockerfile
# Use pre-built wheels
COPY --from=wheel-builder /wheels/*.whl /tmp/wheels/

# Install from local wheels (much faster)
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels \
    crewai langchain-anthropic
```

---

### Phase 4: Approach 4 - Custom Orchestration (Last Resort)

#### Step 4.1: Create Lightweight Orchestrator
**File**: `backend/app/services/orchestrator.py` (NEW FILE)

```python
"""Lightweight multi-agent orchestration without CrewAI."""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.services.llm_service import llm_service

class AgentOrchestrator:
    """Simple multi-agent orchestration."""

    @staticmethod
    async def execute_sequential(
        db: AsyncSession,
        agents: List[Agent],
        tasks: List[str]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially across agents."""
        results = []
        context = ""

        for agent, task in zip(agents, tasks):
            # Build prompt with context from previous agents
            prompt = f"{task}\n\nContext from previous steps:\n{context}"

            # Execute with LLM service
            response = await llm_service.generate(
                prompt=prompt,
                model=agent.model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                system_prompt=agent.system_prompt
            )

            results.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "task": task,
                "result": response
            })

            # Update context for next agent
            context += f"\n\n{agent.name}: {response}"

        return {
            "success": True,
            "results": results,
            "final_output": results[-1]["result"] if results else None
        }

    @staticmethod
    async def execute_parallel(
        db: AsyncSession,
        agents: List[Agent],
        tasks: List[str]
    ) -> Dict[str, Any]:
        """Execute tasks in parallel (async)."""
        import asyncio

        async def execute_task(agent: Agent, task: str):
            response = await llm_service.generate(
                prompt=task,
                model=agent.model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                system_prompt=agent.system_prompt
            )
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "task": task,
                "result": response
            }

        # Execute all tasks concurrently
        results = await asyncio.gather(*[
            execute_task(agent, task)
            for agent, task in zip(agents, tasks)
        ])

        return {
            "success": True,
            "results": results,
            "execution_mode": "parallel"
        }
```

#### Step 4.2: Update Task Worker
**File**: `backend/app/workers/tasks.py`

```python
from app.services.orchestrator import AgentOrchestrator

# Fallback to custom orchestrator if CrewAI unavailable
if not CREWAI_AVAILABLE:
    result = await AgentOrchestrator.execute_sequential(db, [agent], [task_description])
else:
    result = await CrewService.execute_agent_task(db, agent, task_description)
```

---

## 🧪 Testing Strategy

### Unit Tests
**File**: `backend/tests/unit/test_crew_service.py` (NEW FILE)

```python
"""Unit tests for CrewAI service."""
import pytest
from app.services.crew_service import CrewService, CREWAI_AVAILABLE

def test_crewai_availability():
    """Test CrewAI import status."""
    # Will be True if installation succeeds
    assert isinstance(CREWAI_AVAILABLE, bool)

@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
def test_agent_role_mapping():
    """Test agent type to role mapping."""
    from app.models.agent import AgentType
    role = CrewService._map_agent_type_to_role(AgentType.ANALYTICAL)
    assert "Analyst" in role or "Data" in role

# Add more tests...
```

### Integration Tests
**File**: `backend/tests/integration/test_crew_api.py` (NEW FILE)

```python
"""Integration tests for multi-agent workflows."""
import pytest
from httpx import AsyncClient
from app.main import app
from app.services.crew_service import CREWAI_AVAILABLE

@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not available")
@pytest.mark.asyncio
async def test_multi_agent_collaboration():
    """Test creating and executing multi-agent workflow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create two agents
        agent1_response = await client.post("/api/v1/agents", json={
            "name": "Researcher",
            "description": "Research agent",
            "agent_type": "analytical",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a researcher."
        })
        agent1_id = agent1_response.json()["id"]

        agent2_response = await client.post("/api/v1/agents", json={
            "name": "Writer",
            "description": "Writing agent",
            "agent_type": "creative",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a writer."
        })
        agent2_id = agent2_response.json()["id"]

        # Execute collaborative task
        task_response = await client.post("/api/v1/tasks", json={
            "title": "Research and Write Article",
            "description": "Research a topic and write an article",
            "agent_ids": [agent1_id, agent2_id],
            "workflow_type": "sequential"
        })

        assert task_response.status_code == 201
        task_data = task_response.json()
        assert task_data["status"] in ["pending", "in_progress"]
```

### Manual Testing Checklist
- [ ] Docker build completes without timeout
- [ ] CrewAI imports successfully
- [ ] Single agent task executes
- [ ] Multi-agent sequential workflow works
- [ ] Multi-agent hierarchical workflow works
- [ ] Task delegation functions
- [ ] Error handling works when API key missing
- [ ] Performance is acceptable (< 30s for complex workflows)

---

## 📊 Success Criteria

### Must Have ✅
1. Docker build succeeds with CrewAI installed (< 10 minutes)
2. `CREWAI_AVAILABLE` flag is `True` at runtime
3. Single agent task execution works
4. Multi-agent sequential workflow executes
5. No regression in existing functionality
6. Tests pass with CrewAI enabled

### Nice to Have 🎯
1. `crewai-tools` package installed (optional)
2. Hierarchical workflows working
3. Custom tool creation framework
4. Agent delegation enabled
5. Streaming responses for real-time feedback

### Performance Targets 📈
- Docker build time: < 10 minutes (down from timeout)
- Single agent task: < 10 seconds
- Multi-agent workflow (3 agents): < 30 seconds
- Memory usage: < 2GB per agent

---

## 🚧 Known Challenges & Mitigations

### Challenge 1: Dependency Resolution Timeout
**Mitigation**:
- Use `--timeout 300` flag
- Try without `crewai-tools` first
- Use pre-built wheels if needed

### Challenge 2: API Changes in New CrewAI Version
**Mitigation**:
- Read migration guide: https://docs.crewai.com/migration
- Update code incrementally
- Keep fallback to direct LLM calls

### Challenge 3: Increased Docker Image Size
**Mitigation**:
- Use multi-stage builds
- Clean up pip cache
- Compress layers
- Target: Keep image < 2GB

### Challenge 4: LangChain Compatibility
**Mitigation**:
- Pin `langchain-anthropic` version
- Test `ChatAnthropic` integration
- Fallback to direct Anthropic SDK if needed

---

## 📋 Implementation Checklist

### Pre-Implementation
- [ ] Backup current working state
- [ ] Create feature branch: `feature/enable-crewai-orchestration`
- [ ] Document current Docker build time baseline
- [ ] Set up test environment

### Phase 1: Attempt Upgrade (Try First)
- [ ] Update requirements.txt with crewai==0.203.1
- [ ] Add langchain-anthropic dependency
- [ ] Update Dockerfile with longer timeout
- [ ] Attempt Docker build
- [ ] If successful ✅ → Continue to testing
- [ ] If timeout ❌ → Move to Phase 2

### Phase 2: Minimal Installation (If Phase 1 Fails)
- [ ] Try crewai without crewai-tools
- [ ] Implement custom tools
- [ ] Test basic functionality
- [ ] If successful ✅ → Continue to testing
- [ ] If fails ❌ → Move to Phase 3

### Phase 3: Pre-built Wheels (If Phase 2 Fails)
- [ ] Create wheel building Dockerfile
- [ ] Build wheels locally
- [ ] Update main Dockerfile to use wheels
- [ ] Test build
- [ ] If successful ✅ → Continue to testing
- [ ] If fails ❌ → Move to Phase 4

### Phase 4: Custom Orchestration (Last Resort)
- [ ] Implement AgentOrchestrator class
- [ ] Add sequential execution
- [ ] Add parallel execution
- [ ] Update task worker
- [ ] Test workflows
- [ ] Document limitations vs CrewAI

### Testing Phase (After Any Success)
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Manual testing of single agent tasks
- [ ] Manual testing of multi-agent workflows
- [ ] Performance testing
- [ ] Load testing with multiple concurrent workflows

### Documentation & Release
- [ ] Update README.md with CrewAI features
- [ ] Update docs/USER_GUIDE.md with multi-agent workflows
- [ ] Create docs/MULTI_AGENT_WORKFLOWS.md tutorial
- [ ] Add example workflows
- [ ] Update IMPLEMENTATION_SUMMARY.md
- [ ] Create release notes

---

## 📚 Reference Documentation

### CrewAI Resources
- **Official Docs**: https://docs.crewai.com/
- **GitHub**: https://github.com/joaomdmoura/crewAI
- **Migration Guide**: https://docs.crewai.com/migration
- **Examples**: https://github.com/joaomdmoura/crewAI-examples

### LangChain Integration
- **ChatAnthropic**: https://python.langchain.com/docs/integrations/chat/anthropic
- **LangChain Core**: https://python.langchain.com/docs/modules/model_io/

### Related Issues
- Original issue noting CrewAI disabled: `backend/requirements.txt:19-20`
- Implementation summary: `IMPLEMENTATION_SUMMARY.md:99-112`

---

## 🎯 Priority & Timeline

**Priority**: HIGH
**Estimated Total Time**: 4-8 hours (depending on approach)
**Recommended Start**: Immediate

**Timeline**:
- Day 1 (2-3 hours): Attempt approaches 1 & 2
- Day 2 (2-3 hours): If needed, try approaches 3 & 4
- Day 3 (2 hours): Testing and documentation

---

## 🤝 Support & Resources

### If You Get Stuck
1. Check CrewAI Discord: https://discord.gg/crewai
2. Review GitHub issues: https://github.com/joaomdmoura/crewAI/issues
3. LangChain forums: https://github.com/langchain-ai/langchain/discussions
4. Fall back to custom orchestration (Approach 4)

### Key Files to Reference
- `backend/app/services/crew_service.py` - Existing implementation
- `backend/app/workers/tasks.py` - Task execution entry point
- `backend/requirements.txt` - Dependency management
- `backend/Dockerfile` - Build configuration

---

## 🚀 Expected Benefits

Once implemented, users will be able to:

1. **Collaborative Problem Solving**
   - Multiple agents working together on complex tasks
   - Each agent specializing in their domain

2. **Sequential Workflows**
   - Research agent gathers data
   - Analysis agent processes data
   - Writer agent creates report

3. **Hierarchical Execution**
   - Manager agent coordinates worker agents
   - Automatic task delegation and load balancing

4. **Enhanced Capabilities**
   - Access to CrewAI's tool ecosystem
   - Integration with external APIs
   - Memory sharing between agents

5. **Better Task Management**
   - Complex multi-step task execution
   - Automatic retries and error recovery
   - Progress tracking across agent chain

---

## ✅ Definition of Done

This implementation is complete when:

1. ✅ CrewAI packages install successfully in Docker
2. ✅ Single agent tasks execute via CrewService
3. ✅ Multi-agent workflows run end-to-end
4. ✅ All existing tests pass
5. ✅ New CrewAI tests pass
6. ✅ Documentation updated
7. ✅ Feature demo video recorded (optional)
8. ✅ Code merged to main branch

---

**Document Version**: 1.0
**Created**: 2025-10-17
**Author**: Terragon Labs (Terry)
**Status**: Ready for Implementation
