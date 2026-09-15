export const destinations = [
  { path: '/create', title: 'Create', description: 'Your next idea starts here.', detail: 'Compose audio with the configured provider and preserve your lyrics.' },
  { path: '/songs', title: 'My Songs', description: 'Come back to every song you create.', detail: 'Search, play, favorite, and share your saved songs.' },
  { path: '/settings', title: 'Settings', description: 'Make the workspace yours.', detail: 'Choose generation, playback, and export defaults.' },
  { path: '/templates', title: 'Templates', description: 'A little inspiration to get started.', detail: 'Apply an original starting point to your draft.' },
] as const;

export function pageFor(pathname: string) {
  if (pathname === '/') return destinations[0];
  if (/^\/projects\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(pathname)) {
    return { title: 'Project workspace', description: 'Room for every version of your idea.', detail: 'Generate, play, and inspect persistent versions.' };
  }
  if (/^\/songs\/[0-9a-f-]+$/i.test(pathname)) return { title: 'Your song', description: 'Play it, keep it, or create another version.', detail: 'A permanent song page.' };
  return destinations.find(({ path }) => path === pathname);
}
