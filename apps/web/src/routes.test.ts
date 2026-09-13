import { describe, expect, it } from 'vitest';
import { destinations, pageFor } from './routes';

describe('foundation navigation', () => {
  it('resolves every navigation link and the home alias', () => {
    for (const item of destinations) expect(pageFor(item.path)).toEqual(item);
    expect(pageFor('/')).toEqual(pageFor('/create'));
  });
  it('allows UUID project refreshes without inventing project data', () => {
    expect(pageFor('/projects/00000000-0000-4000-8000-000000000001')?.title).toBe('Project workspace');
    expect(pageFor('/projects/not-a-project')).toBeUndefined();
    expect(pageFor('/api/v1/projects')).toBeUndefined();
  });
});
