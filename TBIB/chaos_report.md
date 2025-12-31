| Scénario testé | Résultat | Faille trouvée ? |
|---|---|---|
| Voyageur Temporel (Réserver hier) | Rendez-vous créé avec succès dans le passé. | ❌ FAILLE DÉTECTÉE |
| Le Spammeur (Double Booking) | Crash 500 : Race Condition provoque une erreur DB non gérée. | ❌ FAILLE DÉTECTÉE |
| L'Indécis (Book/Cancel/Book) | Crash DB: Contrainte Unique trop stricte sur les créneaux annulés (SQLite Limitation). | ❌ FAILLE DÉTECTÉE |
| Le Fantôme (Accès non connecté) | Redirection vers Login. | ✅ SÉCURISÉ |
| L'Injecteur (XSS) | Input nettoyé ou échappé. | ✅ SÉCURISÉ |
| L'Espionne (Secrétaire A -> Patient B) | Accès refusé (403) | ✅ SÉCURISÉ |
| La Faussaire (RDV Inexistant) | 404 Not Found. | ✅ SÉCURISÉ |
| Le Dashboard Vide | Affichage correct (200 OK). | ✅ SÉCURISÉ |
| L'Ordonnance Vide | Ordonnance créée sans médicaments. | ❌ FAILLE DÉTECTÉE |
| Le Double Paiement | Accepté deux fois (Idempotent ?). | ✅ SÉCURISÉ |
| L'Oubli de Token | Tous les tokens sont uniques. | ✅ SÉCURISÉ |
