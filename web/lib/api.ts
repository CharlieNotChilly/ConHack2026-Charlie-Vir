export async function generateAidSheet(payload: {
  courseId: string;
  targetPages: number;
  instructions?: string;
}) {
  // [C] TODO: call Next.js API route to generate draft
  return fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
