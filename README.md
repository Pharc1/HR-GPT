# HR-GPT

![HR-GPT Logo](images/logo.png) 

## Description

**HR-GPT** est un assistant virtuel qui automatise l'accès aux politiques d'entreprise. Grâce à l'intelligence artificielle et à l'intégration de modèles Hugging Face, il permet aux employés de poser des questions en langage naturel et d'obtenir des réponses précises à partir de documents internes (politiques de congés, remboursements, etc.).

## Fonctionnalités

- **Base de Connaissances** : Accès aux politiques internes stockées dans Azure Blob Storage.
- **Assistant Conversationnel** : Réponses aux questions courantes grâce à un modèle de langage fine-tuné de Hugging Face.
- **Système de Recommandation** : Suggestions personnalisées basées sur les rôles et les besoins des employés.
- **Notifications** : Alertes sur les mises à jour des politiques et rappels de conformité.
- **Feedback** : Collecte d'avis pour améliorer continuellement le service.

## Technologies Utilisées

- **Langage de Programmation** : Python
- **Framework** : Flask
- **Modèles** : Hugging Face (BERT)
- **Infrastructure Cloud** : Azure pour le déploiement et la gestion des services
- **Stockage** : Azure Blob Storage pour la gestion des documents internes

## Installation


### Étapes d'installation

1. Clonez le repository :

   ```bash
   git clone https://github.com/votre_nom_utilisateur/HR-GPT.git
   cd HR-GPT
   ```

2. Créez un environnement virtuel :

   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

3. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Lancez l'application Flask :

```bash
python app.py
```

Accédez à l'interface utilisateur via [http://localhost:5000](http://localhost:5000).

## Déploiement sur Azure

Pour déployer votre application sur Azure :

1. Créez un compte Azure et configurez Azure App Service.
2. Configurez Azure Blob Storage pour stocker vos documents internes.
3. Suivez les instructions sur la [documentation d'Azure](https://docs.microsoft.com/fr-fr/azure/app-service/quickstart-python) pour déployer une application Flask.

## License

Ce projet est sous la licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contact

Pour toute question, n'hésitez pas à me contacter à l'adresse [kpharci@gmail.com](mailto:kpharci@gmail.com).

![HR-GPT Screenshot](imagesscreenshot.png) 
