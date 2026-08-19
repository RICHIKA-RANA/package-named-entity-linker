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
