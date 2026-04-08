import { useState } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { triggerSync } from '../api';
import { cn } from '../lib/utils';

export function SyncButton() {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState<'success' | 'error' | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setResult(null);
    try {
      await triggerSync();
      setResult('success');
    } catch {
      setResult('error');
    } finally {
      setSyncing(false);
      setTimeout(() => setResult(null), 3000);
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={syncing}
      className={cn(
        'btn-pill text-sm px-4 py-2 transition-all',
        result === 'success'
          ? 'bg-green-100 text-green-700 border border-green-200'
          : result === 'error'
          ? 'bg-red-100 text-red-700 border border-red-200'
          : 'btn-secondary'
      )}
    >
      {syncing ? (
        <>
          <RefreshCw className="w-4 h-4 animate-spin" />
          Sincronizando...
        </>
      ) : result === 'success' ? (
        <>
          <Check className="w-4 h-4" />
          Sincronização iniciada
        </>
      ) : result === 'error' ? (
        <>
          <AlertCircle className="w-4 h-4" />
          Erro ao sincronizar
        </>
      ) : (
        <>
          <RefreshCw className="w-4 h-4" />
          Sincronizar Eventos
        </>
      )}
    </button>
  );
}
