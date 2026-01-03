interface UserMessageProps {
  content: string
}

export function UserMessage({ content }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <div className="rounded-lg bg-secondary px-4 py-2 max-w-[80%]">
        <p className="text-sm text-secondary-foreground whitespace-pre-wrap break-words">
          {content}
        </p>
      </div>
    </div>
  )
}

