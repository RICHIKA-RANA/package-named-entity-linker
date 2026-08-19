export interface Snippet {
  key: string
  title: string
  method: string
  path: string
  js: string
  python: string
}

export function buildSnippets(namespace: string, baseUrl: string): Snippet[] {
  const ns = encodeURIComponent(namespace)
  const entitiesUrl = `${baseUrl}/api/namespaces/${ns}/entities`
  const factsUrl = `${baseUrl}/api/namespaces/${ns}/facts`
  const extractionsUrl = `${baseUrl}/api/namespaces/${ns}/extractions`
  const entityId = 'acme'
  const surfaceTextsUrl = `${entitiesUrl}/${entityId}/surface-texts`
  const regexRulesUrl = `${entitiesUrl}/${entityId}/regex-rules`

  return [
    {
      key: 'list-entities',
      title: 'List entities',
      method: 'GET',
      path: `/api/namespaces/${namespace}/entities`,
      js: `const response = await fetch("${entitiesUrl}");
const entities = await response.json();`,
      python: `import requests

response = requests.get("${entitiesUrl}")
entities = response.json()`,
    },
    {
      key: 'create-entity',
      title: 'Create entity',
      method: 'POST',
      path: `/api/namespaces/${namespace}/entities`,
      js: `const response = await fetch("${entitiesUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    entity_id: "${entityId}",
    label: "Acme Corp",
    surface_texts: ["acme", "acme corp"],
  }),
});
const entity = await response.json();`,
      python: `import requests

response = requests.post(
    "${entitiesUrl}",
    json={
        "entity_id": "${entityId}",
        "label": "Acme Corp",
        "surface_texts": ["acme", "acme corp"],
    },
)
entity = response.json()`,
    },
    {
      key: 'add-surface-text',
      title: 'Add surface text',
      method: 'POST',
      path: `/api/namespaces/${namespace}/entities/${entityId}/surface-texts`,
      js: `const response = await fetch("${surfaceTextsUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ surface_text: "Acme Inc" }),
});
const entity = await response.json();`,
      python: `import requests

response = requests.post(
    "${surfaceTextsUrl}",
    json={"surface_text": "Acme Inc"},
)
entity = response.json()`,
    },
    {
      key: 'add-regex-rule',
      title: 'Add regex rule',
      method: 'POST',
      path: `/api/namespaces/${namespace}/entities/${entityId}/regex-rules`,
      js: `const response = await fetch("${regexRulesUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ regex: "ACME-\\\\d{4}" }),
});
const rule = await response.json();`,
      python: `import requests

response = requests.post(
    "${regexRulesUrl}",
    json={"regex": r"ACME-\\d{4}"},
)
rule = response.json()`,
    },
    {
      key: 'create-fact',
      title: 'Create fact',
      method: 'POST',
      path: `/api/namespaces/${namespace}/facts`,
      js: `const response = await fetch("${factsUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    source: "mayank",
    predicate: "WORKS_AT",
    target: "${entityId}",
    attributes: {},
  }),
});
const fact = await response.json();`,
      python: `import requests

response = requests.post(
    "${factsUrl}",
    json={
        "source": "mayank",
        "predicate": "WORKS_AT",
        "target": "${entityId}",
        "attributes": {},
    },
)
fact = response.json()`,
    },
    {
      key: 'run-extraction',
      title: 'Run extraction',
      method: 'POST',
      path: `/api/namespaces/${namespace}/extractions`,
      js: `const response = await fetch("${extractionsUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message_text: "mayank works at acme",
    word_correction: false,
  }),
});
const result = await response.json();`,
      python: `import requests

response = requests.post(
    "${extractionsUrl}",
    json={
        "message_text": "mayank works at acme",
        "word_correction": False,
    },
)
result = response.json()`,
    },
  ]
}
