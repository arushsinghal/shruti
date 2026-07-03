import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { apiPath } from '../lib/api';

interface Task {
  id: string;
  session_id: string;
  task_type: string;
  title: string;
  status: string;
  owner: string | null;
  due: string | null;
  notes: string | null;
  completed_at: string | null;
  created_at: string;
}

const STATUS_LABEL: Record<string, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  done: 'Done',
  cancelled: 'Cancelled',
};

const TYPE_ICON: Record<string, string> = {
  order_investigations: '🔬',
  follow_up: '📅',
  document_allergy: '⚠️',
  review_prescription: '📋',
  retention_followup_30d: '🔔',
  retention_followup_90d: '🔔',
};

export default function Tasks() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('open');
  const [updating, setUpdating] = useState<string | null>(null);

  const loadTasks = (status: string) => {
    setLoading(true);
    const url = status ? apiPath(`/tasks?status=${status}`) : apiPath('/tasks');
    const token = localStorage.getItem('token');
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => r.json())
      .then(setTasks)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTasks(filter);
  }, [filter]);

  const updateTask = async (taskId: string, status: string) => {
    setUpdating(taskId);
    try {
      const token = localStorage.getItem('token');
      await fetch(apiPath(`/tasks/${taskId}`), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ status }),
      });
      loadTasks(filter);
    } catch (e) {
      console.error(e);
    } finally {
      setUpdating(null);
    }
  };

  const openInvestigationOrder = async (sessionId: string) => {
    try {
      const resp = await api.get(`/sessions/${sessionId}/investigation-order`, {
        responseType: 'text',
        headers: { Accept: 'text/html' },
      });
      const blob = new Blob([resp.data as string], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, '_blank');
      if (win) setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e: any) {
      if (e.response?.status === 409) {
        alert('Confirm at least one fact in the review page before generating the investigation order.');
      } else {
        alert('Failed to open investigation order.');
      }
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', padding: '24px' }}>
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <button
            onClick={() => navigate('/dashboard')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#1B5E3B', fontWeight: 600 }}
          >
            ← Dashboard
          </button>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>
            Work Queue
          </h1>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {['open', 'in_progress', 'done', ''].map((s) => (
            <button
              key={s || 'all'}
              onClick={() => setFilter(s)}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: '1px solid',
                borderColor: filter === s ? '#1B5E3B' : '#D1D5DB',
                background: filter === s ? '#1B5E3B' : '#fff',
                color: filter === s ? '#fff' : '#374151',
                fontWeight: 500,
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              {s ? STATUS_LABEL[s] : 'All'}
            </button>
          ))}
        </div>

        {loading ? (
          <p style={{ color: '#6B7280', textAlign: 'center', padding: 40 }}>Loading tasks…</p>
        ) : tasks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#9CA3AF' }}>
            <p style={{ fontSize: 32 }}>✓</p>
            <p>No {filter} tasks</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {tasks.map((task) => (
              <div
                key={task.id}
                style={{
                  background: '#fff',
                  border: '1px solid #E5E7EB',
                  borderRadius: 10,
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 14,
                }}
              >
                <span style={{ fontSize: 22, flexShrink: 0 }}>
                  {TYPE_ICON[task.task_type] || '📌'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: '0 0 4px', fontWeight: 600, color: '#111827', fontSize: 14 }}>
                    {task.title}
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: '#6B7280' }}>
                    {new Date(task.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                    {task.notes && ` · ${task.notes}`}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0, alignItems: 'center' }}>
                  {task.task_type === 'order_investigations' && task.session_id && (
                    <button
                      onClick={() => openInvestigationOrder(task.session_id)}
                      style={{
                        padding: '4px 10px',
                        background: '#EFF6FF',
                        color: '#1D4ED8',
                        border: '1px solid #BFDBFE',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      View Order
                    </button>
                  )}
                  {task.status === 'open' && (
                    <>
                      <button
                        disabled={updating === task.id}
                        onClick={() => updateTask(task.id, 'done')}
                        style={{
                          padding: '4px 10px',
                          background: '#1B5E3B',
                          color: '#fff',
                          border: 'none',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        Done
                      </button>
                      <button
                        disabled={updating === task.id}
                        onClick={() => updateTask(task.id, 'cancelled')}
                        style={{
                          padding: '4px 10px',
                          background: '#fff',
                          color: '#6B7280',
                          border: '1px solid #D1D5DB',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontSize: 12,
                        }}
                      >
                        Dismiss
                      </button>
                    </>
                  )}
                  {task.status === 'done' && (
                    <span style={{ fontSize: 12, color: '#10B981', fontWeight: 600 }}>✓ Done</span>
                  )}
                  {task.status === 'cancelled' && (
                    <span style={{ fontSize: 12, color: '#9CA3AF' }}>Dismissed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
