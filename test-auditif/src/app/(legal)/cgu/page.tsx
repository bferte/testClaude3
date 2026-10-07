import classNameModule from "@classname";
import styles from "./page.module.scss";
import { Button } from "@ui/common";
import { ArrowLeftIcon } from "lucide-react";
import Link from "next/link";
const className = classNameModule(styles);

export default function Page() {
  return (
    <div {...className("Page")}>
      <Link href={"/"}>
        <Button {...className("backButton")}>
          <ArrowLeftIcon size={18} strokeWidth={3} />
          <span>Retour</span>
        </Button>
      </Link>

      <h1>Politique de protection des données personnelles du groupe Atol</h1>

      <p>
        Le Groupe ATOL est une Coopérative d’opticiens indépendants.
        <br />
        Le bien voir, l’expertise métier et la satisfaction du client sont au
        cœur de nos valeurs et de nos objectifs.
        <br />
        Dans ce cadre, la protection des données personnelles est essentielle et
        un sujet de préoccupation constant chez nous, tout particulièrement du
        fait de l’utilisation de données de santé.
        <br />
        La présente Politique de protection des données personnelles vous
        présente :<br />
      </p>

      <ul>
        <li>
          la manière dont nous collectons, traitons et utilisons vos données
        </li>
        <li>
          les engagements pris par ATOL pour garantir à la fois la sécurité de
          vos données et vos droits.
        </li>
      </ul>

      <h2>
        1. A QUI, À QUOI S’APPLIQUE LA POLITIQUE DE PROTECTION DES DONNÉES
        D’ATOL ?
      </h2>

      <p>
        La présente politique de protection des données personnelles s’applique
        :
      </p>

      <ul>
        <li>
          A la société ATOL SA, société anonyme à capital variable, immatriculée
          au RCS de Nanterre sous le numéro 305 219 859, dont le siège social
          est au 2-6 place du Général de Gaulle – 92160 Antony
        </li>
        <li>
          Aux magasins sous enseigne ATOL situés en France métropolitaine et
          dans les départements et régions et collectivités d’outre-mer
        </li>
      </ul>

      <p>Vos données personnelles peuvent être collectées :</p>

      <ul>
        <li>
          Lors de votre navigation sur nos sites internet{" "}
          <a href="atol.fr">atol.fr</a> et{" "}
          <a href="www.lexilens.com/fr">www.lexilens.com/fr</a>
        </li>
        <li>Lors de votre venue dans un magasin du réseau ATOL</li>
        <li>
          Lorsque vous contactez ATOL et/ou le service client par téléphone,
          courrier ou mail
        </li>
      </ul>

      <h2>2. QUELLES DONNÉES COLLECTONS-NOUS ?</h2>

      <p>
        Nous sommes susceptibles de collecter tout ou partie des données
        suivantes :
      </p>

      <ul>
        <li>
          Les données que vous fournissez en renseignant des formulaires ou
          questionnaires, en téléchargeant des contenus, en souscrivant à des
          services en lignes (pages réseaux sociaux,…)
        </li>
        <li>
          Nom, prénom, adresse postale, adresse électronique, numéro de
          téléphone
        </li>
        <li>Date de naissance, sexe, numéro de sécurité sociale</li>
        <li>Données de connexion (logs, adresse IP, …)</li>
        <li>Opinion sur les produits, les magasins, la marque ATOL</li>
        <li>
          Données commerciales : historique d’achats, offre de services,
          utilisation du SAV, opérations promotionnelles, information de
          paiement
        </li>
        <li>
          Données de santé (taux de prise en charge, prescription, ordonnance,
          dispositifs médicaux)
        </li>
        <li>Photos, vidéos de vous que vous acceptez de partager</li>
        <li>Toute demande particulière que vous pourriez nous adresser</li>
      </ul>

      <h2>3. COMMENT SONT UTILISÉES VOS DONNÉES ?</h2>

      <p>
        Nous utilisons principalement vos données personnelles dans le cadre :
      </p>

      <ul>
        <li>
          de la délivrance des équipements d’optique (commande, télétransmission
          des feuilles de soins à la Sécurité Sociale et aux Organismes
          Complémentaires d’Assurance Maladie) et de leur traçabilité
        </li>
        <li>
          de la gestion commerciale (prospection, fidélisation, action
          marketing)
        </li>
        <li>de la délivrance de services (entretien, réparation, …)</li>
      </ul>

      <h2>
        4. OÙ VOS DONNÉES SONT-ELLES STOCKÉES ET QUELLE EST LEUR DURÉE DE
        CONSERVATION ?
      </h2>

      <p>
        Vos données personnelles sont stockées en France, soit dans nos bases de
        données, soit dans celles de nos prestataires de services. L’ensemble
        des données de santé fait l’objet d’un hébergement chez un prestataire
        agréé de données de santé (HDS).
      </p>
      <p>
        Vos données ne sont conservées que pour la durée strictement nécessaire
        à la réalisation des finalités pour lesquelles elles ont été collectées
        et sont traitées.
      </p>
      <p>Ainsi les données :</p>

      <ul>
        <li>De connexion sont conservées 1 an maximum</li>
        <li>
          Relatives aux documents et pièces comptables sont conservées pendant
          10 ans
        </li>
        <li>
          Relatives aux clients/prospects à des fins d’animation et de
          prospection sont conservées 5 ans maximum
        </li>
        <li>
          Relatives aux équipements d’optique sont conservées jusqu’à 10 ans
          maximum afin d’assurer le service après- vente et les garanties
          proposées par ATOL
        </li>
      </ul>

      <p>
        Une durée plus longue peut être appliquée en cas d’obligations légales
        et/ou réglementaires.
      </p>
      <p>A l’issue de ces durées, les données personnelles sont supprimées.</p>

      <h2>
        5. QUELLES MESURES DE SÉCURITÉ ET DE CONFIDENTIALITÉ ONT ÉTÉ MISES EN
        ŒUVRE ?
      </h2>
      <p>
        Nous avons pour objectif de toujours conserver vos données personnelles
        de la manière la plus sure et la plus sécurisée possible, et uniquement
        pendant la durée nécessaire à leur finalité. Nous avons pris les mesures
        physiques, techniques et organisationnelles pour empêcher, dans la
        mesure du possible, tout accès non autorisé, altération ou perte de vos
        données.
      </p>

      <h2>6. TRANSFÉRONS-NOUS VOS DONNÉES ?</h2>

      <p>
        Vos données personnelles sont destinées à ATOL et aux magasins à
        l’enseigne ATOL. Elles peuvent être transférées :
      </p>
      <p>
        Vos données ne sont conservées que pour la durée strictement nécessaire
        à la réalisation des finalités pour lesquelles elles ont été collectées
        et sont traitées.
      </p>

      <ul>
        <li>
          aux fournisseurs d’équipements optiques aux fins de traitement de vos
          commandes de verres,
        </li>
        <li>
          aux professionnels de santé dans le cadre de contrôle de prescription,
        </li>
        <li>
          à la Sécurité Sociale et aux Organismes Complémentaires d’Assurance
          Maladie pour obtenir vos remboursements,
        </li>
        <li>
          à nos prestataires commerciaux sous-traitants notamment dans le cadre
          d’information sur vos garanties, vos droits et nos offres. Nous nous
          assurons que ces derniers respectent les règles relatives à la
          protection des données personnelles.
        </li>
      </ul>

      <p>
        Vos données ne font pas l’objet d’un transfert dans un pays en dehors de
        l’Union Européenne. Si c’était le cas, vos données continueront de
        bénéficier des mêmes garanties que celles applicables par le RGPD
        (Règlement Général sur la Protection des Données applicable depuis le 25
        mai 2018).
      </p>

      <h2>7. QUELS SONT VOS DROITS ?</h2>

      <p>
        Conformément aux dispositions des articles 15 à 21 du RGPD et de la Loi
        Informatique et Libertés, vous disposez :
      </p>

      <ul>
        <li>D’un droit d’accès</li>
        <li>D’un droit de rectification</li>
        <li>D’un droit d’effacement</li>
        <li>
          D’un droit de limitation et d’opposition sur vos données qui sont
          traitées
        </li>
        <li>D’un droit de modification et/ou de retrait</li>
      </ul>

      <p>
        En cas de décès pour lequel nous avons été informés, vos données sont
        supprimées, sauf celles relevant d’obligations légales et
        réglementaires.
      </p>
      <p>Pour exercer vos droits, il vous suffit de nous contacter (Cf. §8).</p>

      <h2>8. COMMENT NOUS CONTACTER ?</h2>

      <p>
        Pour toute demande de renseignement sur le traitement de vos données
        personnelles et/ou d’exercice de vos droits, vous pouvez contacter ATOL
        :
      </p>

      <ul>
        <li>Par courrier</li>
        <li>Par mail : dpo@atol.fr</li>
      </ul>

      <p>
        Nous vous invitons également à actualiser régulièrement vos données afin
        que nous disposions en permanence de données exactes.
      </p>

      <p>
        Pour toute information relative à la protection des données
        personnelles, vous pouvez consulter le site de la CNIL{" "}
        <a href="www.cnil.fr">www.cnil.fr</a>
      </p>
    </div>
  );
}
