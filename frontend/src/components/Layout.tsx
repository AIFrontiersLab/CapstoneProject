import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { FileQuestion, Upload, FolderOpen } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="app-shell flex flex-col relative">
      {/* Full-page background: z-index -1, opaque */}
      <div className="app-bg" aria-hidden />
      <header className="relative z-10 border-b border-slate-200 bg-white/95 backdrop-blur-sm shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-zinc-800 tracking-tight">
            Enterprise GenAI Document Q&A (Project Capstone)
          </h1>
          <nav className="flex gap-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-700 shadow border border-blue-300/50'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-slate-100 border border-transparent'
                }`
              }
            >
              <FileQuestion className="w-4 h-4" />
              Ask
            </NavLink>
            <NavLink
              to="/upload"
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-700 shadow border border-blue-300/50'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-slate-100 border border-transparent'
                }`
              }
            >
              <Upload className="w-4 h-4" />
              Upload
            </NavLink>
            <NavLink
              to="/documents"
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-700 shadow border border-blue-300/50'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-slate-100 border border-transparent'
                }`
              }
            >
              <FolderOpen className="w-4 h-4" />
              Documents
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="relative z-10 flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}
