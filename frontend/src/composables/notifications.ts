import { reactive } from 'vue'

export interface Notification {
  id: number
  message: string
  ton: 'succes' | 'erreur'
}

const etat = reactive<{ liste: Notification[] }>({ liste: [] })
let compteur = 0

export function useNotifications() {
  function notifier(message: string, ton: Notification['ton'] = 'succes') {
    const id = ++compteur
    etat.liste.push({ id, message, ton })
    setTimeout(() => fermer(id), ton === 'erreur' ? 6000 : 3500)
  }
  function fermer(id: number) {
    etat.liste = etat.liste.filter((n) => n.id !== id)
  }
  return { etat, notifier, fermer }
}
