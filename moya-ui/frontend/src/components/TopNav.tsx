import { Settings } from 'lucide-react'

interface Props {
  activeView: 'builder' | 'marketplace'
  onViewChange: (v: 'builder' | 'marketplace') => void
  onOpenSettings: () => void
}

/** Custom flow-graph icon — three connected nodes representing an agent pipeline */
function MoyaIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      {/* Input node */}
      <circle cx="3.5" cy="10" r="2.5" fill="currentColor" />
      {/* Agent node */}
      <circle cx="10" cy="5" r="2.5" fill="currentColor" />
      {/* Output node */}
      <circle cx="16.5" cy="10" r="2.5" fill="currentColor" />
      {/* input → agent edge */}
      <line x1="5.5" y1="9" x2="8" y2="6.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      {/* agent → output edge */}
      <line x1="12" y1="6.5" x2="14.5" y2="9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      {/* Small arrowheads */}
      <polyline points="7,5.8 8.2,6.4 7.6,7.6" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="14,8 14.6,9 13.4,9.6" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function TopNav({ activeView, onViewChange, onOpenSettings }: Props) {
  return (
    <nav className="h-12 bg-white border-b border-slate-200 flex items-center px-5 flex-shrink-0 z-30">
      {/* Logo — clicking goes back to Builder */}
      <button
        onClick={() => onViewChange('builder')}
        className="flex items-center gap-2.5 mr-6 group"
        aria-label="Moya Agent Studio — go to Builder"
      >
        <div className="w-7 h-7 bg-blue-600 rounded-md flex items-center justify-center text-white group-hover:bg-blue-700 transition-colors">
          <MoyaIcon size={16} />
        </div>
        <span className="text-slate-800 font-semibold text-sm tracking-tight group-hover:text-blue-700 transition-colors">
          Moya Agent Studio
        </span>
      </button>

      {/* Navigation tabs — underline indicator style */}
      <div className="flex items-center h-full">
        <NavTab
          label="Builder"
          active={activeView === 'builder'}
          onClick={() => onViewChange('builder')}
        />
        <NavTab
          label="Marketplace"
          active={activeView === 'marketplace'}
          onClick={() => onViewChange('marketplace')}
        />
      </div>

      <div className="flex-1" />

      <button
        onClick={onOpenSettings}
        title="Settings"
        className="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
      >
        <Settings size={15} />
      </button>
    </nav>
  )
}

function NavTab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={[
        'h-full px-4 text-sm font-medium border-b-2 transition-colors',
        active
          ? 'text-blue-600 border-blue-600'
          : 'text-slate-500 border-transparent hover:text-slate-800 hover:border-slate-300',
      ].join(' ')}
    >
      {label}
    </button>
  )
}
