import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-orange-600 text-white p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold">
          AIチャットボット
        </Link>
        <nav>
          <ul className="flex space-x-4">
            <li>
              <Link href="/about" className="hover:text-orange-200">
                このアプリについて
              </Link>
            </li>
            <li>
              <Link href="/contact" className="hover:text-orange-200">
                お問い合わせ
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}