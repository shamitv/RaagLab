export const destinations = [
  { path: '/create', title: 'Create', description: 'Your next idea starts here.', detail: 'Compose an original instrumental demo and preserve your lyrics.' },
  { path: '/library', title: 'Library', description: 'A home for your finished music.', detail: 'Search and filter completed versions across your projects.' },
  { path: '/projects', title: 'Projects', description: 'Keep your ideas together.', detail: 'Search, reopen, duplicate, and archive your projects.' },
  { path: '/settings', title: 'Settings', description: 'Make the workspace yours.', detail: 'Choose generation, playback, and export defaults.' },
  { path: '/templates', title: 'Templates', description: 'A little inspiration to get started.', detail: 'Apply an original starting point to your draft.' },
] as const;

export function pageFor(pathname: string) {
  if (pathname === '/') return destinations[0];
  if (/^\/projects\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(pathname)) {
    return { title: 'Project workspace', description: 'Room for every version of your idea.', detail: 'Generate, play, and inspect persistent versions.' };
  }
  return destinations.find(({ path }) => path === pathname);
}
