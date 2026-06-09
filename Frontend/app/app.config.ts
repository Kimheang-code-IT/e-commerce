export default defineAppConfig({
  ui: {
    colors: {
      primary: 'blue',
      neutral: 'zinc'
    },
    dashboardPanel: {
      slots: {
        body: 'flex flex-col flex-1 min-h-0 overflow-hidden p-0 m-0 gap-0'
      }
    }
  }
})
