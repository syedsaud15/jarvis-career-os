// Opt-in LOCAL harness only. Not copied into the production image or frontend.
const auditPanel = document.createElement('aside')
auditPanel.id = 'qa-audit'
auditPanel.setAttribute('aria-label', 'Local accessibility audit')
auditPanel.style.cssText = 'position:fixed;right:8px;top:8px;z-index:9999;max-width:90vw;background:white;color:black;border:2px solid #15364e;padding:8px;max-height:60vh;overflow:auto'
const auditButton = document.createElement('button')
auditButton.textContent = 'Run local accessibility audit'
const auditResult = document.createElement('pre')
auditResult.style.cssText = 'white-space:pre-wrap;font:12px monospace'
auditButton.onclick = async () => {
  auditResult.textContent = 'Checking…'
  const result = await window.axe.run({exclude: [['#qa-audit']]}, {runOnly: {type:'tag',values:['wcag2a','wcag21a']}})
  auditResult.textContent = JSON.stringify(result.violations.map(({id,impact,nodes}) => ({id,impact,targets:nodes.map(n=>n.target)})), null, 2)
}
auditPanel.append(auditButton, auditResult)
document.body.append(auditPanel)
