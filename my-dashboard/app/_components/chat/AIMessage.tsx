interface AIMessageProps {
  content: string
}

export function AIMessage({ content }: AIMessageProps) {
  return (
    <div className="flex justify-start">
      <div className="px-4 py-2 max-w-[80%]">
        <p className="text-sm text-foreground whitespace-pre-wrap break-words">
          {content}
        </p>
      </div>
    </div>
  )
}

