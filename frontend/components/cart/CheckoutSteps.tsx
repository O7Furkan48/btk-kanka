export function CheckoutSteps() {
  return (
    <div className="mb-7 flex flex-wrap items-center gap-3">
      <Step n={1} label="Sepetim" active />
      <Sep />
      <Step n={2} label="Adres" />
      <Sep />
      <Step n={3} label="Ödeme" />
    </div>
  );
}

function Step({
  n,
  label,
  active,
}: {
  n: number;
  label: string;
  active?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-[10px] text-[13px] font-semibold ${
        active ? "text-indigo-600" : "text-slate-400"
      }`}
    >
      <span
        className={`inline-flex h-[26px] w-[26px] items-center justify-center rounded-full border-[1.5px] text-xs font-bold ${
          active
            ? "border-indigo-600 bg-indigo-600 text-white shadow-glow"
            : "border-slate-200 bg-slate-100 text-slate-500"
        }`}
      >
        {n}
      </span>
      {label}
    </span>
  );
}

function Sep() {
  return <span aria-hidden className="h-[1.5px] w-7 rounded-sm bg-slate-200" />;
}
