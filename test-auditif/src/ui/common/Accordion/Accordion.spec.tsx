import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import { Accordion } from './Accordion'

describe('Accordion', () => {
    it('should render accordion items', () => {
        render(
            <Accordion>
                <Accordion.Item id="1" label="First Item">
                    <div>Content 1</div>
                </Accordion.Item>
                <Accordion.Item id="2" label="Second Item">
                    <div>Content 2</div>
                </Accordion.Item>
            </Accordion>
        )

        expect(screen.getByText('First Item')).toBeInTheDocument()
        expect(screen.getByText('Second Item')).toBeInTheDocument()
    })

    it('should open and close accordion items when clicked', () => {
        render(
            <Accordion>
                <Accordion.Item id="1" label="First Item">
                    <div>Content 1</div>
                </Accordion.Item>
            </Accordion>
        )

        const header = screen.getByText('First Item')
        expect(screen.queryByText('Content 1')).not.toBeInTheDocument()

        fireEvent.click(header)
        expect(screen.getByText('Content 1')).toBeInTheDocument()

        fireEvent.click(header)
        expect(screen.queryByText('Content 1')).not.toBeInTheDocument()
    })

    it('should close current item when opening another item', () => {
        render(
            <Accordion>
                <Accordion.Item id="1" label="First Item">
                    <div>Content 1</div>
                </Accordion.Item>
                <Accordion.Item id="2" label="Second Item">
                    <div>Content 2</div>
                </Accordion.Item>
            </Accordion>
        )

        fireEvent.click(screen.getByText('First Item'))
        expect(screen.getByText('Content 1')).toBeInTheDocument()
        expect(screen.queryByText('Content 2')).not.toBeInTheDocument()

        fireEvent.click(screen.getByText('Second Item'))
        expect(screen.queryByText('Content 1')).not.toBeInTheDocument()
        expect(screen.getByText('Content 2')).toBeInTheDocument()
    })
}) 