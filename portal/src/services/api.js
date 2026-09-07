/**
 * IDP Control Plane API Client
 */

function getAuthHeaders() {
  const token = localStorage.getItem('idp_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

function generateIdempotencyKey(prefix = 'idemp') {
  return `${prefix}-${crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15)}`;
}

async function handleResponse(res) {
  if (res.status === 401) {
    localStorage.removeItem('idp_token');
    localStorage.removeItem('idp_user');
    window.location.reload();
    throw new Error('Session expired. Please log in again.');
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed with status ${res.status}`);
  }
  return data;
}

export const api = {
  async getTemplates() {
    const res = await fetch('/templates', {
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async submitRequest(payload) {
    const res = await fetch('/requests', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Idempotency-Key': generateIdempotencyKey('req')
      },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async getRequest(requestId) {
    const res = await fetch(`/requests/${requestId}`, {
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async getDeployments(workspace = null) {
    const url = workspace ? `/deployments?workspace=${encodeURIComponent(workspace)}` : '/deployments';
    const res = await fetch(url, {
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async getDeploymentConfig(deploymentId) {
    const res = await fetch(`/deployments/${deploymentId}/config`, {
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async destroyDeployment(deploymentId) {
    const res = await fetch(`/deployments/${deploymentId}/destroy`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Idempotency-Key': generateIdempotencyKey('destroy')
      }
    });
    return handleResponse(res);
  },

  async inspectModelArmor({ text, point = 'prompt', mode = 'block' }) {
    const res = await fetch('/governance/inspect', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ text, point, mode })
    });
    return handleResponse(res);
  },

  async getExpiredDeployments() {
    const res = await fetch('/governance/expired-deployments', {
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async overrideTtl({ deploymentId, extensionDays = 7, reason }) {
    const res = await fetch('/governance/ttl-override', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        deployment_id: deploymentId,
        extension_days: extensionDays,
        reason
      })
    });
    return handleResponse(res);
  },

  async cleanupExpired() {
    const res = await fetch('/governance/cleanup-expired', {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  async queryDeployment({ deploymentId, prompt }) {
    const res = await fetch(`/deployments/${deploymentId}/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ prompt })
    });
    return handleResponse(res);
  }
};
