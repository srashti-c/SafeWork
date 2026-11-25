import React from "react"

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  type?: "text" | "email" | "password" | "date" | "number"
}

export const Input = ({
  type = "text",
  ...props
}: InputProps) => {
  return <input type={type} {...props} />
}