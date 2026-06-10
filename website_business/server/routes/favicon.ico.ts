/** Serve the brand logo for /favicon.ico (search engines check this URL first). */
export default defineEventHandler((event) => {
  return sendRedirect(event, '/image/logo.png', 302)
})
