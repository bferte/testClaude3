import Image from "next/image";
import { Button } from "@ui/common";
import Link from "next/link";

import classNameModule from "@classname";
import styles from "./not-found.module.scss";
const className = classNameModule(styles);

export default function Page() {
  return (
    <div {...className("Page")}>
      <div>
        <Image
          src="/logo.png"
          alt="404"
          {...className("Logo")}
          height={80}
          width={131}
        />
        <h1>Oups, cette page n{"'"}existe pas</h1>

        <div {...className("Actions")}>
          <Link href="/">
            <Button theme="primary">Commencer un test</Button>
          </Link>

          <Link href="/">
            <Button theme="outline">Retourner sur le site</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
