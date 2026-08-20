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
  const entityUrl = `${entitiesUrl}/${entityId}`
  const factId = 'fact-id'
  const factUrl = `${factsUrl}/${factId}`
  const testCasesUrl = `${baseUrl}/api/namespaces/${ns}/test-cases`
  const testCaseId = 'test-case-id'
  const testCaseUrl = `${testCasesUrl}/${testCaseId}`
  const testRunsUrl = `${baseUrl}/api/namespaces/${ns}/test-runs`
  const runId = 'run-id'
  const testRunUrl = `${testRunsUrl}/${runId}`

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
    {
      key: 'update-entity',
      title: 'Update entity',
      method: 'PATCH',
      path: `/api/namespaces/${namespace}/entities/${entityId}`,
      js: `const response = await fetch("${entityUrl}", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ label: "Acme Corporation" }),
});
const entity = await response.json();`,
      python: `import requests

response = requests.patch(
    "${entityUrl}",
    json={"label": "Acme Corporation"},
)
entity = response.json()`,
    },
    {
      key: 'delete-entity',
      title: 'Delete entity',
      method: 'DELETE',
      path: `/api/namespaces/${namespace}/entities/${entityId}`,
      js: `await fetch("${entityUrl}", { method: "DELETE" });`,
      python: `import requests

requests.delete("${entityUrl}")`,
    },
    {
      key: 'bulk-create-entities',
      title: 'Bulk upload entities',
      method: 'POST',
      path: `/api/namespaces/${namespace}/entities/bulk`,
      js: `const response = await fetch("${entitiesUrl}/bulk", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    format: "csv",
    content: "entity_id,label,surface_texts\\n${entityId},Acme Corp,acme|acme corp\\n",
  }),
});
const result = await response.json();`,
      python: `import requests

response = requests.post(
    "${entitiesUrl}/bulk",
    json={
        "format": "csv",
        "content": "entity_id,label,surface_texts\\n${entityId},Acme Corp,acme|acme corp\\n",
    },
)
result = response.json()`,
    },
    {
      key: 'list-regex-rules',
      title: 'List regex rules for an entity',
      method: 'GET',
      path: `/api/namespaces/${namespace}/entities/${entityId}/regex-rules`,
      js: `const response = await fetch("${regexRulesUrl}");
const rules = await response.json();`,
      python: `import requests

response = requests.get("${regexRulesUrl}")
rules = response.json()`,
    },
    {
      key: 'update-regex-rule',
      title: 'Update regex rule',
      method: 'PATCH',
      path: `/api/namespaces/${namespace}/entities/${entityId}/regex-rules`,
      js: `const response = await fetch("${regexRulesUrl}", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ old_regex: "ACME-\\\\d{4}", new_regex: "ACME-\\\\d{5}" }),
});
const rule = await response.json();`,
      python: `import requests

response = requests.patch(
    "${regexRulesUrl}",
    json={"old_regex": r"ACME-\\d{4}", "new_regex": r"ACME-\\d{5}"},
)
rule = response.json()`,
    },
    {
      key: 'delete-regex-rule',
      title: 'Delete regex rule',
      method: 'DELETE',
      path: `/api/namespaces/${namespace}/entities/${entityId}/regex-rules`,
      js: `await fetch("${regexRulesUrl}", {
  method: "DELETE",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ regex: "ACME-\\\\d{4}" }),
});`,
      python: `import requests

requests.delete(
    "${regexRulesUrl}",
    json={"regex": r"ACME-\\d{4}"},
)`,
    },
    {
      key: 'update-fact',
      title: 'Update fact',
      method: 'PATCH',
      path: `/api/namespaces/${namespace}/facts/${factId}`,
      js: `const response = await fetch("${factUrl}", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ predicate: "FOUNDED_BY" }),
});
const fact = await response.json();`,
      python: `import requests

response = requests.patch(
    "${factUrl}",
    json={"predicate": "FOUNDED_BY"},
)
fact = response.json()`,
    },
    {
      key: 'delete-fact',
      title: 'Delete fact',
      method: 'DELETE',
      path: `/api/namespaces/${namespace}/facts/${factId}`,
      js: `await fetch("${factUrl}", { method: "DELETE" });`,
      python: `import requests

requests.delete("${factUrl}")`,
    },
    {
      key: 'create-test-case',
      title: 'Create test case',
      method: 'POST',
      path: `/api/namespaces/${namespace}/test-cases`,
      js: `const response = await fetch("${testCasesUrl}", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message_text: "mayank works at acme",
    word_correction: false,
    expected: [{ surface_text: "mayank", entity_id: "mayank" }],
  }),
});
const testCase = await response.json();`,
      python: `import requests

response = requests.post(
    "${testCasesUrl}",
    json={
        "message_text": "mayank works at acme",
        "word_correction": False,
        "expected": [{"surface_text": "mayank", "entity_id": "mayank"}],
    },
)
test_case = response.json()`,
    },
    {
      key: 'bulk-create-test-cases',
      title: 'Bulk upload test cases',
      method: 'POST',
      path: `/api/namespaces/${namespace}/test-cases/bulk`,
      js: `const response = await fetch("${testCasesUrl}/bulk", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    format: "json",
    content: JSON.stringify([{ message_text: "mayank works at acme" }]),
  }),
});
const result = await response.json();`,
      python: `import requests
import json

response = requests.post(
    "${testCasesUrl}/bulk",
    json={
        "format": "json",
        "content": json.dumps([{"message_text": "mayank works at acme"}]),
    },
)
result = response.json()`,
    },
    {
      key: 'list-test-cases',
      title: 'List test cases',
      method: 'GET',
      path: `/api/namespaces/${namespace}/test-cases`,
      js: `const response = await fetch("${testCasesUrl}");
const cases = await response.json();`,
      python: `import requests

response = requests.get("${testCasesUrl}")
cases = response.json()`,
    },
    {
      key: 'update-test-case',
      title: 'Update test case',
      method: 'PATCH',
      path: `/api/namespaces/${namespace}/test-cases/${testCaseId}`,
      js: `const response = await fetch("${testCaseUrl}", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ expected: [{ surface_text: "mayank", entity_id: "mayank" }] }),
});
const testCase = await response.json();`,
      python: `import requests

response = requests.patch(
    "${testCaseUrl}",
    json={"expected": [{"surface_text": "mayank", "entity_id": "mayank"}]},
)
test_case = response.json()`,
    },
    {
      key: 'delete-test-case',
      title: 'Delete test case',
      method: 'DELETE',
      path: `/api/namespaces/${namespace}/test-cases/${testCaseId}`,
      js: `await fetch("${testCaseUrl}", { method: "DELETE" });`,
      python: `import requests

requests.delete("${testCaseUrl}")`,
    },
    {
      key: 'accept-test-case',
      title: 'Accept test case result as expected',
      method: 'POST',
      path: `/api/namespaces/${namespace}/test-cases/${testCaseId}/accept`,
      js: `const response = await fetch("${testCaseUrl}/accept", { method: "POST" });
const testCase = await response.json();`,
      python: `import requests

response = requests.post("${testCaseUrl}/accept")
test_case = response.json()`,
    },
    {
      key: 'reject-test-case',
      title: 'Reject test case result',
      method: 'POST',
      path: `/api/namespaces/${namespace}/test-cases/${testCaseId}/reject`,
      js: `const response = await fetch("${testCaseUrl}/reject", { method: "POST" });
const testCase = await response.json();`,
      python: `import requests

response = requests.post("${testCaseUrl}/reject")
test_case = response.json()`,
    },
    {
      key: 'create-test-run',
      title: 'Run the test suite',
      method: 'POST',
      path: `/api/namespaces/${namespace}/test-runs`,
      js: `const response = await fetch("${testRunsUrl}", { method: "POST" });
const summary = await response.json();`,
      python: `import requests

response = requests.post("${testRunsUrl}")
summary = response.json()`,
    },
    {
      key: 'list-test-runs',
      title: 'List test runs',
      method: 'GET',
      path: `/api/namespaces/${namespace}/test-runs`,
      js: `const response = await fetch("${testRunsUrl}");
const runs = await response.json();`,
      python: `import requests

response = requests.get("${testRunsUrl}")
runs = response.json()`,
    },
    {
      key: 'get-test-run-results',
      title: 'Get one test run’s results',
      method: 'GET',
      path: `/api/namespaces/${namespace}/test-runs/${runId}`,
      js: `const response = await fetch("${testRunUrl}");
const results = await response.json();`,
      python: `import requests

response = requests.get("${testRunUrl}")
results = response.json()`,
    },
  ]
}
