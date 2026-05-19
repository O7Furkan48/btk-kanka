"use client";

import { useEffect } from "react";
import { Wrench, User } from "lucide-react";
import { useAdminStore } from "@/store/adminStore";

export function AdminToggle() {
  const isAdmin = useAdminStore((s) => s.isAdmin);
  const hydrated = useAdminStore((s) => s.hydrated);
  const hydrate = useAdminStore((s) => s.hydrate);
  const toggleAdmin = useAdminStore((s) => s.toggleAdmin);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!hydrated) {

    return <div className="h-8 w-[120px]" aria-hidden />;
  }

  return (
    <button
      type="button"
      onClick={toggleAdmin}
      title={isAdmin ? "Kullanıcı moduna geç" : "Admin (jüri) moduna geç"}
      className={
        "inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-[12px] font-semibold transition-all " +
        (isAdmin
          ? "border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100"
          : "border-slate-200 bg-white text-slate-600 hover:border-indigo-400 hover:text-indigo-700")
      }
    >
      {isAdmin ? (
        <>
          <Wrench className="h-3.5 w-3.5" />
          <span>Admin</span>
        </>
      ) : (
        <>
          <User className="h-3.5 w-3.5" />
          <span>Kullanıcı</span>
        </>
      )}
    </button>
  );
}
