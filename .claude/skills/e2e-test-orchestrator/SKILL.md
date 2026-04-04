---
name: e2e-test-orchestrator
description: Orchestrate end-to-end testing for DuckDB workflow builder using Playwright. Coordinate test data generation, test case design, workflow validation, and automated test implementation. Splits work across specialized agents (test-data-architect, test-case-strategist, e2e-automation-engineer, workflow-validator) using TeamCreate with parallel execution. Use when: user mentions "E2E testing", "Playwright", "browser automation", "test coverage", "automated testing" for workflow builder, CSV processing, data transformation UI. DOES NOT trigger for: unit testing, API testing, manual testing, performance testing without browser automation.
---

# E2E Test Orchestrator

Comprehensive orchestration of end-to-end testing for the DuckDB workflow builder, coordinating specialized agents to deliver complete test automation infrastructure.

## Orchestrator Responsibilities

As the orchestrator, you coordinate the entire E2E testing workflow:
1. **Plan**: Analyze requirements and create task breakdown
2. **Delegate**: Create agent team and assign tasks via TaskCreate
3. **Monitor**: Track agent progress and resolve blockers
4. **Integrate**: Consolidate agent outputs and validate completeness
5. **Report**: Present final deliverables to the user

## Execution Mode: Agent Team

This orchestrator uses **Agent Team Mode** for parallel execution:

```typescript
// Team composition (4 agents)
TeamCreate(team_name: "e2e-test-team")
  ├── test-data-architect (generates CSV test data)
  ├── test-case-strategist (designs test cases)
  ├── e2e-automation-engineer (implements Playwright tests)
  └── workflow-validator (validates workflow JSON)
```

## Workflow Phases

### Phase 1: Planning & Task Breakdown

**Your Tasks:**
1. Analyze user requirements (E2E testing scope, node types to test, edge cases)
2. Review existing project structure (workflows, tests directory, package.json)
3. Create comprehensive task list with dependencies
4. Identify open questions for user clarification

**TaskCreate Template:**
```typescript
TaskCreate({
  subject: "Generate diverse test CSV data",
  description: "Create test_data_diverse.csv with financial, healthcare, e-commerce segments and edge cases",
  owner: "test-data-architect"
})
```

**Ask User For:**
- Priority: Smoke tests first? Or comprehensive coverage?
- Node types: All node types or specific subset?
- Browser targets: Chrome only? Or Chromium, Firefox, Safari?
- Test execution: CI/CD integration requirements?

### Phase 2: Team Creation & Task Assignment

**Create Team:**
```typescript
TeamCreate({
  team_name: "e2e-test-team",
  description: "E2E testing for DuckDB workflow builder"
})
```

**Spawn Teammates:**
```typescript
// Spawn all 4 teammates in parallel
Agent({ subagent_type: "test-data-architect", name: "test-data-architect", model: "opus", team_name: "e2e-test-team" })
Agent({ subagent_type: "test-case-strategist", name: "test-case-strategist", model: "opus", team_name: "e2e-test-team" })
Agent({ subagent_type: "e2e-automation-engineer", name: "e2e-automation-engineer", model: "opus", team_name: "e2e-test-team" })
Agent({ subagent_type: "workflow-validator", name: "workflow-validator", model: "opus", team_name: "e2e-test-team" })
```

**Assign Tasks via TaskCreate:**
```typescript
// Create tasks with dependencies
TaskCreate({ subject: "Generate test data", owner: "test-data-architect", addBlockedBy: [] })
TaskCreate({ subject: "Design test cases", owner: "test-case-strategist", addBlockedBy: ["Generate test data"] })
TaskCreate({ subject: "Implement Playwright tests", owner: "e2e-automation-engineer", addBlockedBy: ["Design test cases"] })
TaskCreate({ subject: "Validate workflows", owner: "workflow-validator", addBlockedBy: ["Generate test data"] })
```

### Phase 3: Execution Monitoring

**Monitor Progress:**
- Check TaskList periodically for task status
- Respond to teammate SendMessage inquiries
- Unblock teammates waiting on dependencies
- Handle errors and reroute failed tasks

**Teammate Coordination:**
```typescript
// Example: test-data-architect completes data generation
// → Mark task as completed
// → test-case-strategist becomes unblocked
// → test-case-strategist starts designing test cases
```

### Phase 4: Integration & Validation

**Validate Deliverables:**
- [ ] Test data CSV files exist in `/data/`
- [ ] Test case document exists at `/tests/e2e/test_cases.md`
- [ ] Playwright tests exist in `/tests/e2e/*.spec.ts`
- [ ] Workflow JSONs validated in `/data/workflows/`
- [ ] Playwright configured correctly
- [ ] Package.json has test scripts

**Quality Checks:**
- Test data is diverse and includes edge cases
- Test cases cover all node types
- Playwright tests are deterministic and isolated
- Workflow JSONs are valid and loadable

### Phase 5: Final Reporting

**Present Deliverables:**
```
## E2E Testing Harness Complete

### Deliverables
1. Test Data: /data/test_data_diverse.csv (N rows, M columns)
2. Test Cases: /tests/e2e/test_cases.md (X test cases)
3. Playwright Tests: /tests/e2e/ (Y test files)
4. Validation Workflows: /data/workflows/ (Z workflows)

### Test Coverage
- Node Types: input, filter, aggregate, join, SQL, output ✓
- Edge Cases: nulls, special chars, date formats ✓
- Workflows: smoke, happy path, complex multi-node ✓

### Next Steps
1. Run tests: npm run test:e2e
2. View report: open tests/e2e/test-results/index.html
3. Debug: npm run test:e2e -- --debug
```

## Data Delivery Protocol

**File-Based Transfer:**
- Test data: `/data/*.csv` (shared across agents)
- Test cases: `/tests/e2e/test_cases.md` → e2e-automation-engineer
- Playwright tests: `/tests/e2e/*.spec.ts` (final output)
- Workflows: `/data/workflows/*.json` (validated)
- Workspace: `/_workspace/e2e/` (intermediate artifacts)

**Task-Based Coordination:**
- Use TaskCreate to assign work
- Use TaskUpdate to mark completion
- TaskList shows overall progress

**Message-Based Communication:**
- Use SendMessage for real-time coordination
- Broadcast only for critical issues affecting all teammates

## Error Handling Strategy

**Test Data Generation Fails:**
- Create minimal valid dataset
- Log error, continue with test case design
- Flag missing edge cases in test documentation

**Test Case Design Blocked:**
- Use existing workflow JSONs as reference
- Design tests for available node types
- Document gaps for future enhancement

**Playwright Test Fails:**
- Log error with screenshot/video
- Continue with remaining tests
- Report flaky tests for stabilization

**Workflow Validation Fails:**
- Log specific validation error
- Continue with valid workflows
- Flag invalid workflows for manual review

## User Interaction

**Before Delegating:**
- Confirm testing scope (all nodes or subset?)
- Confirm priority (speed or comprehensiveness?)
- Confirm CI/CD requirements (yes/no?)

**During Execution:**
- Report progress at key milestones
- Ask for clarification on blockers
- Present open questions for decision

**After Completion:**
- Present all deliverables
- Explain test coverage achieved
- Provide next steps for execution

## Team Size Guide

For E2E testing harness:
- **Small project** (5-10 test cases): 2-3 teammates
- **Medium project** (10-20 test cases): 3-4 teammates (recommended)
- **Large project** (20+ test cases): 4-5 teammates

Current recommendation: 4 teammates for comprehensive E2E testing.

## Test Scenarios

### Normal Flow
1. User requests E2E testing for workflow builder
2. Orchestrator analyzes requirements, creates task list
3. Team creates test data, test cases, Playwright tests
4. Tests execute successfully, coverage report generated
5. User reviews report, provides feedback

### Error Flow
1. Test data generation fails (edge case too complex)
2. Orchestrator creates fallback dataset, continues
3. Test cases designed with available data
4. Playwright tests skip complex edge case, document gap
5. Final report includes known limitations

## Open Questions to Resolve

**Before Starting:**
- [ ] Node types to test (all or specific?)
- [ ] Browser targets (Chrome only or multi-browser?)
- [ ] CI/CD integration needed?
- [ ] Performance test requirements?
- [ ] Mobile/responsive testing needed?

**During Execution:**
- [ ] Test data sufficient for edge cases?
- [ ] Playwright selectors stable enough?
- [ ] Workflow JSON schema changes needed?

## Success Criteria

- [ ] All 4 agents complete their tasks
- [ ] Test data is diverse and valid
- [ ] Test cases are comprehensive and clear
- [ ] Playwright tests are stable and deterministic
- [ ] Workflow JSONs are validated and documented
- [ ] User can execute tests with single command
- [ ] Test coverage report is generated
