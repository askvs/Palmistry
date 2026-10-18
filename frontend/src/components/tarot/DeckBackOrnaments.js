export default function DeckBackOrnaments() {
  const corners = [
    "left-1.5 top-1.5 border-l-[1.5px] border-t-[1.5px]",
    "right-1.5 top-1.5 border-r-[1.5px] border-t-[1.5px]",
    "bottom-1.5 left-1.5 border-b-[1.5px] border-l-[1.5px]",
    "bottom-1.5 right-1.5 border-b-[1.5px] border-r-[1.5px]",
  ];
  return (
    <>
      {corners.map((c) => (
        <i key={c} aria-hidden="true" className={`absolute h-2.5 w-2.5 rounded-[2px] border-accent-300/75 ${c}`} />
      ))}
      <span aria-hidden="true" className="absolute inset-0 flex items-center justify-center text-accent-300">✦</span>
    </>
  );
}
