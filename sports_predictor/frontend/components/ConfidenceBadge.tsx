import { cn, confidenceColor, confidenceBg } from "@/lib/utils";

interface Props {
  value: number;
  size?: "sm" | "md" | "lg";
}

export default function ConfidenceBadge({ value, size = "md" }: Props) {
  const color = confidenceColor(value);
  const bg = confidenceBg(value);

  return (
    <span
      className={cn(
        "badge font-bold",
        bg,
        color,
        size === "sm" && "text-[10px] px-2 py-px",
        size === "lg" && "text-sm px-3 py-1"
      )}
    >
      {value}%
    </span>
  );
}
