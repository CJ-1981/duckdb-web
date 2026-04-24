import Link from 'next/link';

export default function WorkflowBuilderPage() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Workflow Builder</h1>
        <p className="text-gray-600">Coming soon - use the main page for now</p>
        <Link href="/" className="text-blue-500 hover:underline mt-4 inline-block">
          Go to main page
        </Link>
      </div>
    </div>
  );
}
