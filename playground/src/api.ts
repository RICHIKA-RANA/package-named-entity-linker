export interface Namespace {
  name: string
  description: string | null
  created_at: string
}

export interface Entity {
  entity_id: string
  label: string
  surface_texts: string[]
}

export interface Fact {
  id: string
  source: string
  target: string
  predicate: string
  [key: string]: unknown
}

export interface LinkedEntity {
  entity_id: string
  label: string
  surface_text: string
}

export interface UniversalEntity {
  index: [number, number]
  surface_text: string
  corrected_text: string
  score: number
  entities: LinkedEntity[]
}

export interface RegexEntity {
  index: [number, number]
  surface_text: string
  rule: string
  regex: string
  meronyms: string[]
}

export interface NoTagEntity {
  index: [number, number]
  surface_text: string
}

export interface ExtractionResult {
  universal_entities: UniversalEntity[]
  regex_entities: RegexEntity[]
  no_tag_entities: NoTagEntity[]
}

export interface Commit {
  commit_id: string
  parent_commit_id: string | null
  message: string
  created_at: string
}

export interface CommitDetail extends Commit {
  snapshot: {
    entities: { nodes: unknown[]; edges: unknown[] }
    regex_rules: Record<string, string[]>
  }
}

export interface GraphNode {
  id: string
  label?: string
  surface_texts?: string[]
}

export interface GraphEdge {
  source: string
  target: string
  key: string
  predicate: string
  [key: string]: unknown
}

export interface Graph {
  directed: boolean
  multigraph: boolean
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function safeDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // response body wasn't JSON - fall through to the generic message
  }
  return `Request failed with status ${response.status}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)

  if (!response.ok) {
    throw new ApiError(response.status, await safeDetail(response))
  }

  return response.json() as Promise<T>
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function patchJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(path, init)

  if (!response.ok) {
    throw new ApiError(response.status, await safeDetail(response))
  }
}

function deleteVoid(path: string, body?: unknown): Promise<void> {
  return requestVoid(path, {
    method: 'DELETE',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export function listNamespaces(): Promise<Namespace[]> {
  return request<Namespace[]>('/api/namespaces')
}

export function createNamespace(
  name: string,
  description?: string,
): Promise<Namespace> {
  return postJson<Namespace>('/api/namespaces', { name, description: description || null })
}

export function getNamespace(name: string): Promise<Namespace> {
  return request<Namespace>(`/api/namespaces/${encodeURIComponent(name)}`)
}

export function updateNamespace(name: string, description: string | null): Promise<Namespace> {
  return patchJson<Namespace>(`/api/namespaces/${encodeURIComponent(name)}`, { description })
}

export function deleteNamespace(name: string): Promise<void> {
  return deleteVoid(`/api/namespaces/${encodeURIComponent(name)}`)
}

export function listEntities(namespace: string): Promise<Entity[]> {
  return request<Entity[]>(`/api/namespaces/${encodeURIComponent(namespace)}/entities`)
}

export function createEntity(
  namespace: string,
  entityId: string,
  label: string,
  surfaceTexts: string[],
): Promise<Entity> {
  return postJson<Entity>(`/api/namespaces/${encodeURIComponent(namespace)}/entities`, {
    entity_id: entityId,
    label: label || null,
    surface_texts: surfaceTexts,
  })
}

export interface BulkUploadResult {
  created: number
  errors: { row: number; error: string }[]
}

export function updateEntity(
  namespace: string,
  entityId: string,
  updates: { label?: string; surface_texts?: string[] },
): Promise<Entity> {
  return patchJson<Entity>(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}`,
    updates,
  )
}

export function deleteEntity(namespace: string, entityId: string): Promise<void> {
  return deleteVoid(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}`,
  )
}

export function bulkCreateEntities(
  namespace: string,
  format: 'csv' | 'json',
  content: string,
): Promise<BulkUploadResult> {
  return postJson<BulkUploadResult>(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/bulk`,
    { format, content },
  )
}

export function listRegexRules(namespace: string, entityId: string): Promise<string[]> {
  return request<string[]>(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}/regex-rules`,
  )
}

export function updateRegexRule(
  namespace: string,
  entityId: string,
  oldRegex: string,
  newRegex: string,
): Promise<{ entity_id: string; regex: string }> {
  return patchJson(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}/regex-rules`,
    { old_regex: oldRegex, new_regex: newRegex },
  )
}

export function deleteRegexRule(
  namespace: string,
  entityId: string,
  regex: string,
): Promise<void> {
  return deleteVoid(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}/regex-rules`,
    { regex },
  )
}

export function addSurfaceText(
  namespace: string,
  entityId: string,
  surfaceText: string,
): Promise<Entity> {
  return postJson<Entity>(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}/surface-texts`,
    { surface_text: surfaceText },
  )
}

export function addRegexRule(
  namespace: string,
  entityId: string,
  regex: string,
): Promise<{ entity_id: string; regex: string }> {
  return postJson(
    `/api/namespaces/${encodeURIComponent(namespace)}/entities/${encodeURIComponent(entityId)}/regex-rules`,
    { regex },
  )
}

export function listFacts(namespace: string): Promise<Fact[]> {
  return request<Fact[]>(`/api/namespaces/${encodeURIComponent(namespace)}/facts`)
}

export function createFact(
  namespace: string,
  source: string,
  predicate: string,
  target: string,
): Promise<Fact> {
  return postJson<Fact>(`/api/namespaces/${encodeURIComponent(namespace)}/facts`, {
    source,
    predicate,
    target,
    attributes: {},
  })
}

export function updateFact(
  namespace: string,
  factId: string,
  updates: { predicate?: string; attributes?: Record<string, unknown> },
): Promise<Fact> {
  return patchJson<Fact>(
    `/api/namespaces/${encodeURIComponent(namespace)}/facts/${encodeURIComponent(factId)}`,
    updates,
  )
}

export function deleteFact(namespace: string, factId: string): Promise<void> {
  return deleteVoid(
    `/api/namespaces/${encodeURIComponent(namespace)}/facts/${encodeURIComponent(factId)}`,
  )
}

export function commitNamespace(namespace: string, message: string): Promise<Commit> {
  return postJson<Commit>(`/api/namespaces/${encodeURIComponent(namespace)}/commits`, { message })
}

export function listCommits(namespace: string): Promise<Commit[]> {
  return request<Commit[]>(`/api/namespaces/${encodeURIComponent(namespace)}/commits`)
}

export function getCommit(namespace: string, commitId: string): Promise<CommitDetail> {
  return request<CommitDetail>(
    `/api/namespaces/${encodeURIComponent(namespace)}/commits/${encodeURIComponent(commitId)}`,
  )
}

export function rollbackNamespace(namespace: string, commitId: string): Promise<Commit> {
  return postJson<Commit>(
    `/api/namespaces/${encodeURIComponent(namespace)}/commits/${encodeURIComponent(commitId)}/rollback`,
    {},
  )
}

export function getGraph(namespace: string): Promise<Graph> {
  return request<Graph>(`/api/namespaces/${encodeURIComponent(namespace)}/graph`)
}

export interface ExpectedPair {
  surface_text: string
  entity_id: string
}

export interface TestCase {
  id: string
  namespace: string
  message_text: string
  word_correction: boolean
  expected: ExpectedPair[] | null
  review_status: 'pending' | 'accepted' | 'rejected'
  created_at: string
}

export interface TestRun {
  id: string
  namespace: string
  created_at: string
  triggering_commit_id: string | null
}

export interface TestRunResult {
  id: string
  run_id: string
  test_case_id: string
  actual: ExpectedPair[]
  passed: boolean | null
  status_label: 'pass' | 'regression' | 'fixed' | 'fail' | 'new' | 'needs_review'
}

export interface TestRunSummary {
  run: TestRun
  results: TestRunResult[]
  accuracy: number | null
  graded_count: number
  passed_count: number
  total_count: number
}

export function createTestCase(
  namespace: string,
  messageText: string,
  wordCorrection: boolean,
  expected?: ExpectedPair[],
): Promise<TestCase> {
  return postJson<TestCase>(`/api/namespaces/${encodeURIComponent(namespace)}/test-cases`, {
    message_text: messageText,
    word_correction: wordCorrection,
    expected: expected ?? null,
  })
}

export function bulkCreateTestCases(
  namespace: string,
  format: 'csv' | 'json',
  content: string,
): Promise<BulkUploadResult> {
  return postJson<BulkUploadResult>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-cases/bulk`,
    { format, content },
  )
}

export function listTestCases(namespace: string): Promise<TestCase[]> {
  return request<TestCase[]>(`/api/namespaces/${encodeURIComponent(namespace)}/test-cases`)
}

export function updateTestCase(
  namespace: string,
  testCaseId: string,
  updates: {
    message_text?: string
    word_correction?: boolean
    expected?: ExpectedPair[] | null
    review_status?: string
  },
): Promise<TestCase> {
  return patchJson<TestCase>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-cases/${encodeURIComponent(testCaseId)}`,
    updates,
  )
}

export function deleteTestCase(namespace: string, testCaseId: string): Promise<void> {
  return deleteVoid(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-cases/${encodeURIComponent(testCaseId)}`,
  )
}

export function acceptTestCase(namespace: string, testCaseId: string): Promise<TestCase> {
  return postJson<TestCase>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-cases/${encodeURIComponent(testCaseId)}/accept`,
    {},
  )
}

export function rejectTestCase(namespace: string, testCaseId: string): Promise<TestCase> {
  return postJson<TestCase>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-cases/${encodeURIComponent(testCaseId)}/reject`,
    {},
  )
}

export function createTestRun(namespace: string): Promise<TestRunSummary> {
  return postJson<TestRunSummary>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-runs`,
    {},
  )
}

export function listTestRuns(namespace: string): Promise<TestRun[]> {
  return request<TestRun[]>(`/api/namespaces/${encodeURIComponent(namespace)}/test-runs`)
}

export function getTestRunResults(namespace: string, runId: string): Promise<TestRunResult[]> {
  return request<TestRunResult[]>(
    `/api/namespaces/${encodeURIComponent(namespace)}/test-runs/${encodeURIComponent(runId)}`,
  )
}

export function runExtraction(
  namespace: string,
  messageText: string,
  wordCorrection: boolean,
): Promise<ExtractionResult> {
  return postJson<ExtractionResult>(
    `/api/namespaces/${encodeURIComponent(namespace)}/extractions`,
    { message_text: messageText, word_correction: wordCorrection },
  )
}
